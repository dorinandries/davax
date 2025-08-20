from fastapi import APIRouter, Depends, Request, Response, HTTPException
from typing import Optional
from ..schemas import ChatRequest, ChatResponse
from ..profanity import is_offensive
from ..rag import retrieve
from ..openai_client import client
from ..config import settings
from ..tokens_logger import log_request, log_response
from ..logging_utils import app_logger
from ..routers._helpers import get_current_user_optional
from ..rate_limit import anon_used_count, mark_anon_used, ANON_LIMIT
import uuid


router = APIRouter(prefix="/chat", tags=["chat"])
log = app_logger()


BOOK_SUMMARIES = {}


# Încarcă rezumate complete (tool source) la startup
from pathlib import Path
import json
summ_path = Path(__file__).resolve().parent.parent / "data" / "book_summaries.json"
if summ_path.exists():
    try:
        BOOK_SUMMARIES = json.loads(summ_path.read_text(encoding="utf-8"))
    except Exception:
        BOOK_SUMMARIES = {}


def get_summary_by_title(title: str) -> str:
    return BOOK_SUMMARIES.get(title, "Rezumat indisponibil pentru acest titlu.")

TOOLS = [
    {
    "type": "function",
    "function": {
        "name": "get_summary_by_title",
        "description": "Returnează rezumatul complet pentru un titlu de carte exact.",
        "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                },
                "required": ["title"]
            }
        }
    }
]


SYSTEM_PROMPT = (
    "Ești Smart Librarian. Primești preferințe/teme și recomanzi o singură carte. "
    "Explică pe scurt de ce se potrivește (2-3 fraze). După recomandare, apelează function calling 'get_summary_by_title' cu titlul exact. "
    "Dacă nu ai context suficient, cere o clarificare. Răspunde în română."
)


def _ensure_anon_cookie(request: Request, response: Response) -> str:
    sid = request.cookies.get("anon_session_id")
    if not sid:
        sid = str(uuid.uuid4())
        response.set_cookie("anon_session_id", sid, httponly=True, samesite="lax")
    return sid


@router.get("/anon-status")
async def anon_status(request: Request, response: Response):
    sid = _ensure_anon_cookie(request, response)
    used = anon_used_count(sid)
    remaining = max(0, ANON_LIMIT - used)
    if remaining == 0:
        msg = "Neautentificat: Nu mai ai autentificari gratuite. Creează cont pentru acces nelimitat."
    elif remaining == 1:
        msg = "Neautentificat: ai 1 recomandare gratuită. Creează cont pentru acces nelimitat."
    else:
        msg = f"Neautentificat: ai {remaining} recomandari gratuite. Creează cont pentru acces nelimitat."
    return {"remaining": remaining, "message": msg}


@router.post("/recommend", response_model=ChatResponse)
async def recommend(payload: ChatRequest, request: Request, response: Response, user = Depends(get_current_user_optional)):
    query = (payload.query or "").strip()
    # Verificare limbaj nepotrivit – NU contorizează utilizarea gratuită
    if is_offensive(query):
        log.warning(f"Offensive text blocked: {query}")
        return ChatResponse(status="blocked", message="Mesajul conține limbaj necorespunzător. Încearcă altă formulare.")

    # Limită 2 recomandări pe zi pentru anonimi
    current_user = user
    if not current_user:
        sid = _ensure_anon_cookie(request, response)
        used = anon_used_count(sid)
        remaining = max(0, ANON_LIMIT - used)
        if remaining == 0:
            msg = "Neautentificat: Nu mai ai autentificari gratuite. Creează cont pentru acces nelimitat."
            return ChatResponse(status="forbidden", message=msg)
        elif remaining == 1:
            msg = "Neautentificat: ai 1 recomandare gratuită. Creează cont pentru acces nelimitat."
        else:
            msg = f"Neautentificat: ai {remaining} recomandari gratuite. Creează cont pentru acces nelimitat."

    # RAG: retrieve contexte
    contexts = retrieve(query, k=3)
    if not contexts:
        # NU contorizează ca utilizare reușită anon
        return ChatResponse(status="no_results", message="Nu am găsit cărți potrivite. Încearcă cu alte teme/chei.")

    # Construim prompt cu contexte
    ctx_text = "\n\n".join([c["chunk"] for c in contexts])
    candidate_titles = [c.get("title") for c in contexts if c.get("title")]
    candidate_titles_text = (
        "Titluri candidate: " + ", ".join(candidate_titles) if candidate_titles else ""
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
        {
            "role": "assistant",
            "content": f"Contexte candidate (RAG):\n{ctx_text}\n\n{candidate_titles_text}",
        },
    ]

    # Prima rundă – modelul face recomandarea și cere tool call
    try:
        comp = client.chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3
        )
    except Exception as e:
        log.exception(f"OpenAI error: {e}")
        return ChatResponse(status="error", message="A apărut o eroare la model. Încearcă din nou.")

    choice = comp.choices[0]
    usage = comp.usage or None
    in_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
    out_tok = getattr(usage, "completion_tokens", 0) if usage else 0

    user_label = current_user["email"] if current_user else request.cookies.get("anon_session_id", "anon")
    log_request(user_label, query, settings.chat_model, in_tok, out_tok)

    tool_calls = choice.message.tool_calls or []

    # 1) Adaugă assistant message cu tool_calls ca DICT-uri simple (nu obiecte SDK)
    assistant_msg = {
        "role": "assistant",
        "content": choice.message.content or "",
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in tool_calls
        ],
    }
    messages.append(assistant_msg)

    summary_text: Optional[str] = None
    recommended_title: Optional[str] = None

    # 2) Execută TOATE tool-urile și răspunde la fiecare tool_call_id
    for tc in tool_calls:
        name = tc.function.name
        try:
            args = json.loads(tc.function.arguments or "{}")
        except Exception:
            args = {}

        if name == "get_summary_by_title":
            recommended_title = args.get("title")

            # Normalizează titlul pentru matching robust
            def match_title(t):
                t_norm = t.strip().casefold()
                for key in BOOK_SUMMARIES.keys():
                    if key.strip().casefold() == t_norm:
                        return key
                return None

            matched_title = match_title(recommended_title)
            tool_output = get_summary_by_title(matched_title or recommended_title)
            summary_text = tool_output

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,  # IMPORTANT: exact id-ul primit
            "name": name,
            "content": tool_output or "",
        })

    # 3) A doua completare (răspunsul final)
    try:
        comp2 = client.chat.completions.create(
            model=settings.chat_model,
            messages=messages,
            temperature=0.2,
        )
    except Exception as e:
        log.exception(f"OpenAI error(2): {e}")
        return ChatResponse(status="error", message="Eroare la generarea răspunsului final.")
    choice2 = comp2.choices[0]
    usage2 = comp2.usage or None
    in_tok2 = getattr(usage2, "prompt_tokens", 0) if usage2 else 0
    out_tok2 = getattr(usage2, "completion_tokens", 0) if usage2 else 0
    log_response(user_label, choice2.message.content or "", settings.chat_model, in_tok2, out_tok2)
    final_text = choice2.message.content or ""

    # Marcare utilizare reușită pentru anonimi (după ce avem recomandare/rezumat)
    if not current_user:
        sid = request.cookies.get("anon_session_id")
        if sid and (recommended_title or final_text):
            mark_anon_used(sid)

    return ChatResponse(
    status="success",
    message=final_text,
    recommended_title=recommended_title,
    summary=summary_text
    )
