import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from scipy.optimize import minimize

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Conv1D, Bidirectional, LSTM, GlobalAveragePooling1D, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import kerastuner as kt

# 1. Încărcare date
df = pd.read_csv('dataset2.csv')
X, y = df['text'].values, df['author'].map({'EAP':0,'HPL':1,'MWS':2}).values
X_test = pd.read_csv('test.csv')['text'].values

# 2. Split pentru validare internă
X_tr, X_val, y_tr, y_val = train_test_split(
    X, y, stratify=y, test_size=0.2, random_state=42
)

# 3. Pipeline + RandomizedSearchCV pentru TF-IDF + LogisticRegression
pipe = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf',   LogisticRegression(max_iter=2000))
])
param_dist = {
    'tfidf__ngram_range': [(1,1), (1,2), (1,3)],
    'tfidf__max_features': [20000, 50000, 100000],
    'clf__C':             [0.01, 0.1, 1, 10],
    'clf__solver':        ['lbfgs','saga']
}
search_lr = RandomizedSearchCV(
    pipe, param_dist,
    n_iter=20, cv=5,
    scoring='neg_log_loss',
    verbose=1, n_jobs=-1, random_state=42
)
search_lr.fit(X_tr, y_tr)
best_lr = search_lr.best_estimator_
pA_val = best_lr.predict_proba(X_val)

# 4. Pregătire secvențe pentru modele neuronale
MAX_WORDS, MAX_LEN = 20000, 100
tok = Tokenizer(num_words=MAX_WORDS)
tok.fit_on_texts(X_tr)
seq_tr  = pad_sequences(tok.texts_to_sequences(X_tr),  maxlen=MAX_LEN)
seq_val = pad_sequences(tok.texts_to_sequences(X_val), maxlen=MAX_LEN)

# 5. Keras Tuner pentru MLP simplu
def build_mlp(hp):
    model = Sequential([
        Embedding(
            input_dim=MAX_WORDS,
            output_dim=hp.Choice('emb_dim_mlp',[50,100,200])
        ),
        GlobalAveragePooling1D(),
        Dropout(hp.Float('dropout1_mlp',0.2,0.6,step=0.1)),
        Dense(hp.Int('dense_units_mlp',32,128,step=32), activation='relu'),
        Dropout(hp.Float('dropout2_mlp',0.2,0.6,step=0.1)),
        Dense(3, activation='softmax'),
    ])
    model.compile(
        optimizer=hp.Choice('opt_mlp',['adam','rmsprop']),
        loss='sparse_categorical_crossentropy'
    )
    return model

es = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
rlp = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2)

tuner_mlp = kt.RandomSearch(
    build_mlp,
    objective='val_loss',
    max_trials=10,
    executions_per_trial=1,
    directory='mlp_tuner',
    project_name='authorship_mlp'
)
# Apel corect la tuner.search cu batch_size fix
tuner_mlp.search(
    seq_tr, y_tr,
    validation_data=(seq_val, y_val),
    epochs=10,
    batch_size=32,
    callbacks=[es, rlp]
)
best_mlp = tuner_mlp.get_best_models(num_models=1)[0]
pB_val = best_mlp.predict(seq_val)

# 6. Keras Tuner pentru CNN + BiLSTM
def build_cnn_lstm(hp):
    model = Sequential()
    model.add(Embedding(
        MAX_WORDS,
        hp.Choice('emb_dim_cnn',[50,100,200])
    ))
    if hp.Boolean('use_conv'):
        model.add(Conv1D(
            filters=hp.Int('filters_cnn',32,128,step=32),
            kernel_size=hp.Choice('kernel_cnn',[3,5,7]), activation='relu'
        ))
    if hp.Boolean('use_lstm'):
        model.add(Bidirectional(LSTM(
            hp.Int('lstm_units_cnn',16,64,step=16),
            return_sequences=True
        )))
    model.add(GlobalAveragePooling1D())
    model.add(Dropout(hp.Float('dropout_cnn',0.2,0.6,step=0.1)))
    model.add(Dense(3, activation='softmax'))
    model.compile(
        optimizer=hp.Choice('opt_cnn',['adam','rmsprop']),
        loss='sparse_categorical_crossentropy'
    )
    return model


tuner_cnn = kt.RandomSearch(
    build_cnn_lstm,
    objective='val_loss',
    max_trials=10,
    executions_per_trial=1,
    directory='cnn_tuner',
    project_name='authorship_cnn'
)
# Apel corect la tuner.search cu batch_size fix
tuner_cnn.search(
    seq_tr, y_tr,
    validation_data=(seq_val, y_val),
    epochs=10,
    batch_size=32,
    callbacks=[es, rlp]
)
best_cnn = tuner_cnn.get_best_models(num_models=1)[0]
pC_val = best_cnn.predict(seq_val)

# 7. Optimizare greutăți ensemble
def ensemble_loss(w):
    w1, w2 = w
    w3 = 1 - w1 - w2
    p = w1*pA_val + w2*pB_val + w3*pC_val
    return log_loss(y_val, p)

cons = ({'type':'ineq','fun': lambda w: w[0]},
        {'type':'ineq','fun': lambda w: w[1]},
        {'type':'ineq','fun': lambda w: 1-w[0]-w[1]})
res = minimize(ensemble_loss, [0.4,0.3], constraints=cons)
w1_opt, w2_opt = res.x; w3_opt = 1 - w1_opt - w2_opt

print("Ensemble weights:", w1_opt, w2_opt, w3_opt)
print("Log-loss ensemble optimizat:", res.fun)

# 8. Re-antrenare finală pe tot setul și predicție test
# TF-IDF + LR
best_lr.fit(X, y)
pA_test = best_lr.predict_proba(X_test)

# MLP
full_seq = pad_sequences(tok.texts_to_sequences(X), maxlen=MAX_LEN)
best_mlp.fit(
    full_seq, y,
    epochs=5,
    batch_size=32,
    callbacks=[es, rlp]
)
pB_test = best_mlp.predict(pad_sequences(tok.texts_to_sequences(X_test), maxlen=MAX_LEN))

# CNN+BiLSTM
best_cnn.fit(
    full_seq, y,
    epochs=5,
    batch_size=32,
    callbacks=[es, rlp]
)
pC_test = best_cnn.predict(pad_sequences(tok.texts_to_sequences(X_test), maxlen=MAX_LEN))

# Ensemble final
p_test = w1_opt*pA_test + w2_opt*pB_test + w3_opt*pC_test

# Salvare submission
sub = pd.DataFrame(p_test, columns=['EAP','HPL','MWS'])
sub.insert(0, 'id', pd.read_csv('test.csv')['id'])
sub.to_csv('dataset2_submission_abc_pipeline.csv', index=False)
