# 📚 NouSmartLibrarian – AI Book Recommendation Platform

NouSmartLibrarian este o aplicație full-stack care folosește inteligența artificială pentru a recomanda cărți, oferind rezumate detaliate, teme și gestionarea preferințelor utilizatorilor. Platforma combină un backend rapid (FastAPI + Chroma + OpenAI) cu un frontend modern (React + Vite + Material UI).

---

## Funcționalități principale

- **Recomandări AI personalizate:** Chatbot care sugerează cărți relevante pe baza preferințelor și istoricului conversației.
- **RAG + LLM:** Pipeline ce filtrează limbajul, folosește retrieval augmented generation și tool calling pentru rezumate detaliate.
- **Rezumat & teme:** Pentru fiecare carte, primești un rezumat și temele principale (ex: identitate, iubire, aventură).
- **Autentificare & management cont:** Înregistrare, login, resetare parolă cu OTP pe email, logout, status autentificare.
- **Preferințe utilizator:** Setează și salvează genurile preferate pentru recomandări mai relevante.
- **Limitare pentru anonimi:** Utilizatorii neautentificați primesc o singură recomandare gratuită.
- **Observabilitate:** Loguri detaliate pentru evenimente și costuri API.
- **Admin tools:** Endpointuri pentru curățare rapidă a datelor (users, preferences, db) cu rol sau secret.
- **Frontend modern:** UI responsive, chat interactiv, feedback instant, TTS (text-to-speech) pentru răspunsuri.

---

## Setup rapid

### 1. Clonare proiect

```sh
git clone https://github.com/username/NouSmartLibrarian.git
cd NouSmartLibrarian
```

### 2. Backend

```sh
cd backend
python -m venv .venv
.venv/bin/activate  # sau .venv\Scripts\activate pe Windows
pip install -r requirements.txt
```

#### 3. Configurare `.env`

Creează fișierul `.env` în directorul `backend/` cu următorul conținut (modifică valorile cu datele tale):

```
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_ORIGIN=http://localhost:5173
ENV=dev

JWT_SECRET=schimba_cu_un_secret_random
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

SQLITE_URL=sqlite:///./app.db

REDIS_URL=redis://localhost:6379/0
OTP_TTL_SECONDS=600
OTP_SEND_COOLDOWN_SECONDS=60
OTP_RATE_LIMIT_PER_HOUR=50

ADMIN_SECRET=schimba_cu_un_secret_admin
ADMIN_BOOTSTRAP_ENABLED=true
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@email.com
ADMIN_PASSWORD=Admin123!
ADMIN_OVERWRITE_PASSWORD=false

SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=xxxxxxx
SMTP_PASS=xxxxxxx
SMTP_FROM="Smart Librarian <hello@demomailtrap.co>"

OPENAI_API_KEY=sk-...
CHAT_MODEL=gpt-4.1-nano
EMBEDDING_MODEL=text-embedding-3-small

PRICE_CHAT_INPUT=0.0001
PRICE_CHAT_OUTPUT=0.0004
PRICE_EMBEDDING=0.00002
```

**Notă:**  
- Pentru email, poți folosi [Mailtrap](https://mailtrap.io/) sau orice SMTP real.
- Pentru OpenAI, introdu cheia ta personală.

#### 4. Pornește Redis

```sh
docker run -p 6379:6379 redis:7-alpine
```

#### 5. Rulează backend-ul

```sh
uvicorn app.main:app --reload
```

#### 6. Populează baza de date cu rezumate

La primul apel către `/chat/recommend` se creează colecția Chroma. Pentru populare masivă, rulează în consola proiectului:

```sh
python app/seed_chroma.py
```

---

### 7. Frontend

```sh
cd ../frontend
npm install
npm run dev
```

---


## Baze de date folosite

### 1. SQLite
- **Rol:** Persistența datelor de utilizator, autentificare, preferințe, loguri și administrare.
- **De ce SQLite?** Este rapid, ușor de integrat cu FastAPI, nu necesită server separat și e ideal pentru prototipare sau aplicații cu volum mediu de date.
- **Utilizare:** Toate operațiile CRUD pentru utilizatori, preferințe, loguri și administrare se fac prin SQLite (`backend/app.db`).

### 2. ChromaDB
- **Rol:** Vector store pentru embedding-uri AI, folosit la căutarea semantică și recomandări de cărți.
- **De ce Chroma?** E optimizat pentru stocarea și interogarea embedding-urilor, are integrare nativă cu OpenAI și permite retrieval rapid pentru pipeline-ul RAG.
- **Utilizare:** Stochează embedding-uri pentru rezumate și metadate cărți, folosit la recomandări și căutări contextuale (`backend/chroma/chroma.sqlite3`).

### 3. Redis
- **Rol:** Cache și stocare temporară pentru OTP, rate-limit și sesiuni.
- **De ce Redis?** E extrem de rapid, ideal pentru operații temporare, rate-limit și management OTP.
- **Utilizare:** Folosit pentru generare și validare OTP, limitare acces și cooldown la resetare parolă.

## Structură proiect

- `backend/` – API, loguri, seed, Chroma, SQLite, Redis, date, configurare
- `frontend/` – React, pagini, context, stiluri, API client

---

## Securitate & Observabilitate

- Token-uri JWT cu refresh automat.
- Rate-limit și cooldown pentru OTP.
- Loguri detaliate în `logs/`.
- Endpointuri admin protejate cu rol sau secret.

---

## Extensii viitoare

- Recomandări pe baza genurilor preferate preluate din profilul utilizatorilor.
- Istoric conversații.
- Export preferințe și recomandări.
- Integrare cu alte modele AI.

---

## Demonstrarea funcționalității aplicației

### 1. Recomandări fără cont (free trial)
Imaginile de mai jos arată cum un utilizator neautentificat poate primi maxim 3 recomandări de cărți:

![Free trial 1](demo/free_trial_chat_recommendation_1.jpg)
![Free trial 2](demo/free_trial_chat_recommendation_2.jpg)
![Free trial 3](demo/free_trial_chat_recommendation_3.jpg)

### 2. Chat ca user autentificat
După autentificare, utilizatorul are acces la recomandări nelimitate și la funcționalități suplimentare:

![Chat autentificat 1](demo/auth_conversation_1.jpg)
![Chat autentificat 2](demo/auth_conversation_2.jpg)

### 3. Creare cont cu verificare email
Procesul de înregistrare implică introducerea emailului, primirea unui cod de verificare și confirmarea adresei:

![Register 1](demo/register_1.jpg)
![Register 2](demo/register_2.jpg)
![Register 3](demo/register_3.jpg)

### 4. Resetare parolă cu verificare email
La resetarea parolei, se introduce emailul, se primește codul de validare, apoi se setează noua parolă:


![Resetare parolă 1](demo/reset_password_1.jpg)
![Resetare parolă 2](demo/reset_password_2.jpg)
![Resetare parolă 3](demo/reset_password_3.jpg)
