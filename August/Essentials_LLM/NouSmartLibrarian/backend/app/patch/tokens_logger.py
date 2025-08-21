
from __future__ import annotations
import os, datetime, json
from pathlib import Path

PRICES = {
    "gpt-4.1-nano": {"in": 0.0004, "out": 0.0016},
}

def _paths():
    today = datetime.datetime.now().strftime("%d-%m-%Y")
    base = Path("logs") / today
    (base / "tokens").mkdir(parents=True, exist_ok=True)
    base.mkdir(parents=True, exist_ok=True)
    return base / "tokens" / "tokens.log", base / "app.log"

def _calc_cost(model: str, in_tok: int, out_tok: int) -> float:
    p = PRICES.get(model) or PRICES.get(model.lower()) or {"in": 0.0, "out": 0.0}
    return (in_tok / 1000.0) * p["in"] + (out_tok / 1000.0) * p["out"]

def log_request(user: str, prompt: str, model: str, in_tok: int, out_tok: int):
    f_tokens, _ = _paths()
    cost = _calc_cost(model, in_tok, out_tok)
    rec = [user, prompt, f"{cost:.6f}", datetime.datetime.now().isoformat()]
    with open(f_tokens, "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "request", "data": rec}, ensure_ascii=False) + "\n")

def log_response(user: str, content: str, model: str, in_tok: int, out_tok: int):
    f_tokens, _ = _paths()
    cost = _calc_cost(model, in_tok, out_tok)
    rec = [user, content, f"{cost:.6f}", datetime.datetime.now().isoformat()]
    with open(f_tokens, "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "response", "data": rec}, ensure_ascii=False) + "\n")
