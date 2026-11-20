"""Split a page's text at its punctuation (. and :) instead of the printed lines. Bedjan's footnotes (lines that
begin with a note number, "1)" or a page/variant number) are kept apart. uv run segments.py PAGE prints them."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTE = re.compile(r"^\s*(\d+\)|\d+\s)")


def segments(page: int) -> tuple[list[str], list[str]]:
    lines = [ln.strip().replace("‏", "") for ln in (ROOT / "data" / "text" / f"p{page:03d}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    body = [ln for ln in lines if not NOTE.match(ln)]
    notes = [ln for ln in lines if NOTE.match(ln)]
    text = " ".join(body)
    parts = [s.strip() for s in re.split(r"(?<=[.:])\s+", text) if s.strip()]
    return parts, notes


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    segs, notes = segments(int(sys.argv[1]))
    for i, s in enumerate(segs):
        print(i, s)
    for n in notes:
        print("NOTE", n)
