"""English translation of the whole book with Gemini 3.8 Flash (chosen in translate_test.py), one call per page.
  OPENROUTER_KEY_FILE=... uv run translate_book.py [--workers 8] [--model google/gemini-3.8-flash]
Resumable: a page with data/translation/pNNN.json is skipped (p. 1 keeps the pilot by Claude). The page's segments and
notes go in one list; the answer must have the same length, or the page is tried once more and then skipped (logged).
Progress: one line per page with its cost, and the running total, flushed. Translate again after an OCR change: delete
the page's file (build_site.py shows a page without English when the segments no longer match).
"""
import argparse
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from segments import segments
from translate_test import PROMPT, call

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "translation"
lock = threading.Lock()
total = [0.0, 0]


def one(page: int, model: str) -> None:
    out = OUT / f"p{page:03d}.json"
    if out.exists():
        return
    segs, notes = segments(page)
    items = segs + notes
    if not items:
        return
    prompt = PROMPT.format(page=page, n=len(items), segs=json.dumps([[i + 1, s] for i, s in enumerate(items)], ensure_ascii=False))
    if notes:
        prompt += f"\n(Segments {len(segs) + 1}-{len(items)} are Bedjan's footnotes: variant readings of the manuscripts.)"
    for attempt in (1, 2):
        try:
            text, secs, cost = call(model, "low", prompt)
        except Exception as e:
            print(f"p. {page}: FAILED {e}", flush=True)
            time.sleep(10)
            continue
        m = re.search(r"\[.*\]", text, re.S)
        try:
            en = json.loads(m.group()) if m else []
        except Exception:
            en = []
        with lock:
            total[0] += cost
        if len(en) == len(items) and all(isinstance(x, str) for x in en):
            out.write_text(json.dumps({"by": f"{model} (machine translation of the OCR text, 20-Nov-2026; not checked)",
                                       "segments": en[:len(segs)], "notes": en[len(segs):]}, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            with lock:
                total[1] += 1
                print(f"[{time.strftime('%H:%M:%S')}] p. {page}: {len(items)} segments, {secs:.0f} s, ${cost:.4f}; "
                      f"{total[1]} pages, ${total[0]:.3f} so far", flush=True)
            return
        print(f"p. {page}: answer has {len(en)} items for {len(items)} (attempt {attempt})", flush=True)
    print(f"p. {page}: SKIPPED", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--workers", type=int, default=8)
    a.add_argument("--model", default="google/gemini-3.8-flash")
    a = a.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pages = sorted(int(p.stem[1:]) for p in (ROOT / "data" / "text").glob("p*.txt"))
    todo = [p for p in pages if not (OUT / f"p{p:03d}.json").exists()]
    print(f"{len(todo)} pages to translate", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(lambda p: one(p, a.model), todo))
    left = [p for p in pages if not (OUT / f"p{p:03d}.json").exists()]
    print(f"finished: {total[1]} pages translated, ${total[0]:.3f}; {len(left)} pages without English {left[:30]}", flush=True)


if __name__ == "__main__":
    main()
