"""Which model should translate the Chronography? A test of cost, speed and accuracy (20-Nov-2026).
  OPENROUTER_KEY_FILE=... uv run translate_test.py run [model ...]    -> data/translate_test/MODEL_pNNN.json
  uv run translate_test.py table                                     -> cost and time per model
Each page is sent in one call: its punctuation segments (segments.py), numbered, as JSON; the answer is a JSON list of
the same length. The OCR text has known errors (a lost first letter of a printed line, some wrong letters): the model is
asked to translate the evident sense and mark a doubtful reading with {OCR?}. Accuracy is judged afterwards by reading.
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from segments import segments

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "translate_test"
PAGES = [1, 128, 250]
MODELS = {
    "opus": ("anthropic/claude-opus-5.5", "low"),
    "sonnet": ("anthropic/claude-sonnet-5.5", "low"),
    "haiku": ("anthropic/claude-haiku-5.5", None),
    "flash": ("google/gemini-3.8-flash", "low"),
    "argon": ("google/gemini-4-argon", "low"),
    "gpt": ("openai/gpt-6.1-sol", "low"),
}
PROMPT = """You translate Syriac into English. The text is page {page} of the Chronography (Chronicon Syriacum) of Gregory
Barhebraeus (1226-1286), in Paul Bedjan's vocalised edition (Paris 1890), as read by OCR. The OCR has errors: the first
letter of a printed line is sometimes lost (e.g. ܕܝܢܬܐ for ܡܕܝܢܬܐ), and a few letters are misread; the page header
(a title and page number) may be in the first segment. Translate the evident sense; where a reading is doubtful, translate
the likely word and add {{OCR?}}. Keep names in their usual English form (Abu'l-Faraj, Melitene, Constantine). Address God
with modern "You/Your". Keep the segments as they are: one English segment for each Syriac segment, in order; a segment
may be an incomplete phrase.

Segments (JSON list of [number, Syriac]):
{segs}

Answer with JSON only: a list of {n} strings, the English of segments 1 to {n}."""


def call(model: str, effort: str | None, prompt: str) -> tuple[str, float, float]:
    key = Path(os.environ["OPENROUTER_KEY_FILE"]).read_text(encoding="utf-8").strip()
    body = {"model": model, "max_tokens": 12000, "messages": [{"role": "user", "content": prompt}], "usage": {"include": True}}
    if effort:
        body["reasoning"] = {"effort": effort}
    t = time.time()
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": "Bearer " + key},
                      json=body, timeout=600)
    d = r.json()
    if not r.ok or "error" in d:
        raise RuntimeError(f"HTTP {r.status_code}: {str(d.get('error', d))[:300]}")
    return d["choices"][0]["message"]["content"] or "", time.time() - t, (d.get("usage") or {}).get("cost") or 0.0


def one(name: str, page: int) -> str:
    out = OUT / f"{name}_p{page:03d}.json"
    if out.exists():
        return f"{name} p. {page}: done already"
    segs, _ = segments(page)
    model, effort = MODELS[name]
    prompt = PROMPT.format(page=page, n=len(segs), segs=json.dumps([[i + 1, s] for i, s in enumerate(segs)], ensure_ascii=False))
    try:
        text, secs, cost = call(model, effort, prompt)
    except Exception as e:
        return f"{name} p. {page}: FAILED {e}"
    m = re.search(r"\[.*\]", text, re.S)
    try:
        en = json.loads(m.group()) if m else []
    except Exception:
        en = []
    out.write_text(json.dumps({"model": model, "effort": effort, "page": page, "seconds": round(secs, 1), "cost": cost,
                               "n_segments": len(segs), "n_answers": len(en), "english": en, "raw": text if not en else ""},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    return f"{name} p. {page}: {len(en)}/{len(segs)} segments, {secs:.0f} s, ${cost:.4f}"


def table() -> None:
    rows = {}
    for f in OUT.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        name = f.stem.rsplit("_", 1)[0]
        r = rows.setdefault(name, {"cost": 0.0, "secs": 0.0, "segs": 0, "ok": 0, "pages": 0})
        r["cost"] += d["cost"]; r["secs"] += d["seconds"]; r["segs"] += d["n_segments"]
        r["ok"] += d["n_answers"] == d["n_segments"]; r["pages"] += 1
    print(f"{'model':8} {'pages':>5} {'aligned':>8} {'cost':>9} {'$/1000 seg':>11} {'s/page':>7}")
    for k, r in sorted(rows.items(), key=lambda x: x[1]["cost"]):
        print(f"{k:8} {r['pages']:5d} {r['ok']:8d} {r['cost']:9.4f} {1000 * r['cost'] / max(r['segs'], 1):11.2f} {r['secs'] / r['pages']:7.0f}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1] == "run":
        names = sys.argv[2:] or list(MODELS)
        with ThreadPoolExecutor(9) as ex:
            for line in ex.map(lambda a: one(*a), [(n, p) for n in names for p in PAGES]):
                print(line, flush=True)
    else:
        table()
