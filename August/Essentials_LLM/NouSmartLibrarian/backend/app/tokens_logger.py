from datetime import datetime
from .config import settings
from .logging_utils import TokensLogger


_tokens = TokensLogger()


def usd_cost_chat(inp_tokens: int, out_tokens: int) -> float:
    return (inp_tokens / 1000.0) * settings.price_chat_input + (out_tokens / 1000.0) * settings.price_chat_output


def usd_cost_embed(tokens: int) -> float:
    return (tokens / 1000.0) * settings.price_embedding


def log_request(user: str, content: str, model: str, in_tokens: int, out_tokens: int):
    _tokens.log({
        "ts": datetime.utcnow().isoformat(),
        "direction": "request",
        "user": user,
        "model": model,
        "content": content,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "usd_cost": "{:.6f}".format(usd_cost_chat(in_tokens, out_tokens))
    })


def log_response(user: str, content: str, model: str, in_tokens: int, out_tokens: int):
    _tokens.log({
        "ts": datetime.utcnow().isoformat(),
        "direction": "response",
        "user": user,
        "model": model,
        "content": content,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "usd_cost": "{:.6f}".format(usd_cost_chat(in_tokens, out_tokens))
    })


def log_embedding(user: str, input_preview: str, tokens: int):
    _tokens.log({
        "ts": datetime.utcnow().isoformat(),
        "direction": "embedding",
        "user": user,
        "model": settings.embedding_model,
        "content": input_preview[:200],
        "input_tokens": tokens,
        "output_tokens": 0,
        "usd_cost": "{:.6f}".format(usd_cost_embed(tokens))
    })