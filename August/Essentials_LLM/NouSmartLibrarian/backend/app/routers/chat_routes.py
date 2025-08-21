
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from typing import Optional, List, Dict, Any
import json, re

from ..patch.profanity import is_offensive
from ..patch.rate_limit import anon_used_count, mark_anon_used, ANON_LIMIT
from ..patch.logging_utils import app_logger
from ..patch.tokens_logger import log_request, log_response
from ..patch.conversation_state import get_ctx, update_ctx

try:
    from ..rag import retrieve
    def retrieve_candidates(q: str, k: int):
        return retrieve(q, k=k) or []
except Exception:
    from ..patch.rag_adapter import retrieve_filtered
    from ..patch.data_loader import TITLE_KEYS
    def retrieve_candidates(q: str, k: int):
        return retrieve_filtered(q, allowed_titles=TITLE_KEYS, k=k)

try:
    from ..routers._helpers import get_current_user_optional
except Exception:
    def get_current_user_optional():
        return None

try:
    from ..config import settings
except Exception:
    class _S: chat_model="gpt-4.1-nano"
    settings=_S()

try:
    from ..openai_client import client
except Exception:
    raise RuntimeError("openai_client.client indisponibil – păstrează clientul existent din proiect.")

from ..schemas import ChatRequest, ChatResponse

from ..patch.data_loader import BOOK_JSON, BOOK_MD, TITLE_KEYS, get_summary_by_title
from ..patch.intent import classify
from ..patch.book_kb import get_pages, get_author, get_year
from ..patch.title_match import match_title_key
log = app_logger()
router = APIRouter(prefix="/chat", tags=["chat"])


def allowed_titles() -> List[str]:
    return sorted(TITLE_KEYS, key=lambda s: s.lower())


def shortlist_from_rag(query: str, k: int = 5) -> List[str]:
    res = retrieve_candidates(query, k=k)
    titles, seen = [], set()
    for r in res:
        t = (r.get("title") or "").strip()
        if not t: continue
        if t in seen: continue
        if t in TITLE_KEYS:
            seen.add(t);
            titles.append(t)
    return titles


SYSTEM_PROMPT = (
    "Ești Smart Librarian. Recomandă O SINGURĂ carte **doar din inventarul local**.\n"
    "După recomandare, **apelează** obligatoriu tool-ul get_summary_by_title cu titlul EXACT.\n"
    "Dacă utilizatorul se referă la 'prima/a doua/a treia carte sugerată', înțelege că referința e la lista "
    "din ultimul tău răspuns. Menține contextul conversației.\n"
    "Dacă nu ai suficiente informații, cere o clarificare scurtă. Răspunde în română.\n"
    "Ești restricționat la subiecte despre cărți din inventarul local.Nu oferi cod, funcții, sfaturi de programare, nici alte informații în afara domeniului.Pentru solicitări în afara domeniului, răspunde politicos că nu e în aria ta."
)


def ensure_anon_cookie(request: Request, response: Response) -> str:
    sid = request.cookies.get("anon_session_id")
    if not sid:
        import uuid
        sid = "anon-" + uuid.uuid4().hex[:16]
        response.set_cookie("anon_session_id", sid, httponly=True, samesite="lax")
    return sid


def build_tools_schema() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Returnează rezumatul complet pentru un titlu din inventarul local.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "enum": allowed_titles(),
                            "description": "Alege exact un titlu din lista disponibilă."
                        }
                    },
                    "required": ["title"],
                    "additionalProperties": False
                }
            }
        }
    ]


def detect_ordinal_ref(text: str) -> Optional[int]:
    s = (text or "").lower()
    if "prima" in s or "primă" in s: return 1
    if "a doua" in s: return 2
    if "a treia" in s: return 3
    if "a patra" in s: return 4
    return None


@router.get("/anon-status")
async def anon_status(request: Request, response: Response):
    sid = ensure_anon_cookie(request, response)
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
async def recommend(payload: ChatRequest, request: Request, response: Response,
                    user=Depends(get_current_user_optional)):
    q = (payload.query or "").strip()
    if not q:
        raise HTTPException(400, "Mesajul este gol.")
    current_user = user
    if not current_user:
        sid = ensure_anon_cookie(request, response)
        if anon_used_count(sid) >= ANON_LIMIT:
            return ChatResponse(status="blocked",
                                message="Limita gratuită a fost atinsă. Creează cont pentru acces nelimitat.")

    if is_offensive(q):
        return ChatResponse(status="offensive", message="Mesajul conține limbaj nepotrivit. Reformulează te rog.")

    # Intent routing (server-side guardrails)
    intent = classify(q)
    if intent == "out_of_scope":
        return ChatResponse(
            status="out_of_scope",
            message="Îmi pare rău, pot răspunde doar la întrebări despre cărți din inventarul bibliotecii. Încearcă să formulezi o întrebare despre o carte sau o recomandare."
        )
    # Ordinal handled below via detect_ordinal_ref
    if intent == "book_followup":
        ctx_id = f"user:{current_user['id']}" if current_user else f"anon:{request.cookies.get('anon_session_id')}"
        ctx = get_ctx(ctx_id)
        last_title = ctx.get("last_selected_title") or ctx.get("last_recommended_title")
        if not last_title:
            return ChatResponse(status="need_title",
                                message="La ce carte te referi? Spune-mi titlul ca să te pot ajuta.")
        # pages / author / year from local metadata only
        lower_q = q.lower()
        if "pagin" in lower_q:
            pages = get_pages(last_title)
            if pages:
                return ChatResponse(status="success", message=f"„{last_title}” are {pages} pagini.",
                                    recommended_title=last_title, summary=None)
            else:
                return ChatResponse(status="success",
                                    message=f"Nu am local numărul de pagini pentru „{last_title}”. Pot însă să-ți ofer rezumatul sau alte recomandări.",
                                    recommended_title=last_title, summary=None)
        if "autor" in lower_q or "scris" in lower_q:
            author = get_author(last_title)
            if author:
                return ChatResponse(status="success", message=f"„{last_title}” este scrisă de {author}.",
                                    recommended_title=last_title, summary=None)
            else:
                return ChatResponse(status="success",
                                    message=f"Nu am local autorul pentru „{last_title}”. Pot să-ți ofer rezumatul sau alte recomandări.",
                                    recommended_title=last_title, summary=None)
        if "anul" in lower_q or "publicat" in lower_q or "aparit" in lower_q:
            year = get_year(last_title)
            if year:
                return ChatResponse(status="success", message=f"„{last_title}” a fost publicată în {year}.",
                                    recommended_title=last_title, summary=None)
            else:
                return ChatResponse(status="success",
                                    message=f"Nu am local anul apariției pentru „{last_title}”. Pot să-ți ofer rezumatul sau alte recomandări.",
                                    recommended_title=last_title, summary=None)
        # Default follow-up about the selected book: provide summary again (safe and useful)
        summary_text = get_summary_by_title(last_title)
        return ChatResponse(status="success", message=f"Despre „{last_title}”: iată rezumatul pe scurt.",
                            recommended_title=last_title, summary=summary_text)
        return ChatResponse(status="offensive", message="Mesajul conține limbaj nepotrivit. Reformulează te rog.")

    ctx_id = f"user:{current_user['id']}" if current_user else f"anon:{request.cookies.get('anon_session_id')}"
    ctx = get_ctx(ctx_id)
    last_options: List[str] = ctx.get("last_shortlist") or []

    ord_idx = detect_ordinal_ref(q)
    if ord_idx and 1 <= ord_idx <= len(last_options):
        chosen_title = last_options[ord_idx - 1]
        summary = get_summary_by_title(chosen_title)
        msg = f"Cartea aleasă este „{chosen_title}”. Iată rezumatul detaliat:"
        if not current_user:
            mark_anon_used(request.cookies.get("anon_session_id"))
        return ChatResponse(status="success", message=msg, recommended_title=chosen_title, summary=summary)

    shortlist = shortlist_from_rag(q, k=5)
    if not shortlist:
        return ChatResponse(status="no_results", message="Nu am găsit cărți potrivite în inventarul local.")
    update_ctx(ctx_id, last_shortlist=shortlist)

    candidate_text = "Candidați disponibili: " + ", ".join(shortlist)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": q},
        {"role": "assistant", "content": f"{candidate_text}\nAlege doar din acești candidați și apoi apelează tool-ul."}
    ]

    tools = build_tools_schema()

    try:
        comp = client.chat.completions.create(
            model=settings.chat_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )
    except Exception as e:
        log.exception(f"OpenAI err: {e}")
        return ChatResponse(status="error", message="A apărut o eroare la model.")

    ch = comp.choices[0]
    usage = comp.usage or None
    in_tok = getattr(usage, "prompt_tokens", 0) if usage else 0
    out_tok = getattr(usage, "completion_tokens", 0) if usage else 0

    user_label = (current_user["email"] if current_user else request.cookies.get("anon_session_id", "anon"))
    log_request(user_label, q, settings.chat_model, in_tok, out_tok)

    tool_calls = ch.message.tool_calls or []
    assistant_msg = {
        "role": "assistant",
        "content": ch.message.content or "",
        "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in tool_calls
        ],
    }
    messages.append(assistant_msg)

    recommended_title: Optional[str] = None
    summary_text: Optional[str] = None
    tool_msgs: List[Dict[str, Any]] = []

    for tc in tool_calls:
        if tc.function.name == "get_summary_by_title":
            try:
                args = json.loads(tc.function.arguments or "{}")
            except Exception:
                args = {}
            raw = args.get("title") or ""
            key = match_title_key(raw, TITLE_KEYS)
            if key:
                recommended_title = key
                summary_text = get_summary_by_title(key)
                update_ctx(ctx_id, last_selected_title=recommended_title, last_recommended_title=recommended_title)
                tool_msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": "get_summary_by_title",
                    "content": summary_text,
                })

    if not tool_calls:
        recommended_title = shortlist[0]
        summary_text = get_summary_by_title(recommended_title)
        update_ctx(ctx_id, last_selected_title=recommended_title, last_recommended_title=recommended_title)
        tool_msgs.append({
            "role": "tool",
            "tool_call_id": "manual",
            "name": "get_summary_by_title",
            "content": summary_text,
        })

    messages.extend(tool_msgs)

    try:
        comp2 = client.chat.completions.create(
            model=settings.chat_model,
            messages=messages,
            temperature=0.2,
        )
    except Exception as e:
        log.exception(f"OpenAI err(2): {e}")
        return ChatResponse(status="error", message="Eroare la generarea răspunsului final.")

    ch2 = comp2.choices[0]
    usage2 = comp2.usage or None
    in_tok2 = getattr(usage2, "prompt_tokens", 0) if usage2 else 0
    out_tok2 = getattr(usage2, "completion_tokens", 0) if usage2 else 0
    log_response(user_label, ch2.message.content or "", settings.chat_model, in_tok2, out_tok2)

    final_text = ch2.message.content or ""

    if not recommended_title:
        low = final_text.lower()
        for t in TITLE_KEYS:
            if t.lower() in low:
                recommended_title = t
                break

    if (not recommended_title) and shortlist:
        recommended_title = shortlist[0]
        update_ctx(ctx_id, last_selected_title=recommended_title, last_recommended_title=recommended_title)

    if recommended_title and not summary_text:
        summary_text = get_summary_by_title(recommended_title)
    update_ctx(ctx_id, last_selected_title=recommended_title, last_recommended_title=recommended_title)

    if not current_user:
        sid = request.cookies.get("anon_session_id")
        if sid and (recommended_title or final_text):
            mark_anon_used(sid)

    return ChatResponse(
        status="success",
        message=final_text,
        recommended_title=recommended_title,
        summary=summary_text,
    )
