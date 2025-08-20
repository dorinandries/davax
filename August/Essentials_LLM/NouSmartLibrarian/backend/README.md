# Smart Librarian – Backend


## Setup rapid
1. `python -m venv .venv`
2. `.venv/bin/activate`
3. `pip install -r requirements.txt`
4. Creează fișierul `.env` în directorul `backend/` cu următorul conținut:
   ```plaintext
   SECRET_KEY=change_me
   OPENAI_API_KEY=sk-...
   SQLITE_URL=sqlite+aiosqlite:///./smartlibrarian.db
   REDIS_URL=redis://localhost:6379/0
   OPENAI_CHAT_MODEL=gpt-4o-mini
   OPENAI_EMBED_MODEL=text-embedding-3-small
   ```
   Asigură-te că înlocuiești `sk-...` cu cheia ta OpenAI
5. Pornește Redis (`docker run -p 6379:6379 redis:7-alpine`).
6. Rulează API: `uvicorn app.main:app --reload`.
7. (Opțional) Initializează Chroma: primul apel `/chat/recommend` va crea colecția; pentru populare masivă, citește `data/book_summaries.*` și apelează `rag.add_books` într-un mic script.


## Endpointuri
- `POST /auth/send-otp?email=` – trimite cod, cu cooldown și rate‑limit.
- `POST /auth/verify-otp` – verifică `email`, `code`.
- `POST /auth/register` – creează utilizator (pasul 2), validare parolă.
- `POST /auth/login` – login cu email sau username; setează cookie‑uri `access_token` și `refresh_token` (HttpOnly).
- `POST /auth/refresh` – reînnoiește access token (din refresh cookie).
- `POST /auth/logout` – șterge cookie‑urile.
- `GET /auth/me` – status autentificare.
- `POST /auth/preferences` – setează genuri preferate (pentru extensii ulterioare RAG).
- `POST /chat/recommend` – pipeline: filtrare limbaj → RAG → LLM → tool calling `get_summary_by_title` → rezultat.


## Observabilitate
- `logs/DD-MM-YYYY/app.log` – evenimente app.
- `logs/DD-MM-YYYY/tokens/tokens.log` – fiecare call, cu cost USD estimat.


## Note proiectare
- Limitarea 1 recomandare pentru anonimi se face pe cookie `anon_session_id` + Redis (`anon:used:{sid}`). Numai un răspuns `success` marchează consumul; mesaje `blocked/no_results/error` **nu** consumă.
- Filtrarea limbajului e server‑side, înainte de LLM; nu se trimite promptul mai departe când e ofensator.
- Tool calling: modelul recomandă cartea, apoi apelează funcția locală cu titlul exact pentru a returna rezumatul detaliat.
- Costuri: calcule pe baza tarifelor din `.env` – evităm hardcodare.