"""OCR of the whole book: data/raw/jp2/**/ketabademadatbez00barhuoft_LLLL.jp2 (download_book.ps1) -> data/text/pNNN.txt.
  uv run ocr_book.py [--workers 3] [--first 1 --last 598]
Resumable: a page whose data/text/pNNN.txt exists is skipped. Each worker converts its pages to JPEG
(data/raw/bedjan_pNNN.jpg, as in the pilot) and runs Kraken on 10 pages per call (ocr_kraken.run), so the models load
once per 10 pages. Printed page = 605 - leaf. Progress: one line per batch, with the time, flushed.
"""
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

import ocr_kraken

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
TEXT = ROOT / "data" / "text"


def jp2_of(leaf: int) -> Path | None:
    hits = list((RAW / "jp2").rglob(f"*_{leaf:04d}.jp2"))
    return hits[0] if hits else None


def prepare(page: int) -> bool:
    jpg = RAW / f"bedjan_p{page:03d}.jpg"
    if jpg.exists():
        return True
    src = jp2_of(605 - page)
    if not src:
        return False
    Image.open(src).convert("L").save(jpg, quality=92)
    return True


def worker(pages: list[int], wid: int, total: int, done: list[int]) -> None:
    for i in range(0, len(pages), 10):
        batch = [p for p in pages[i:i + 10] if prepare(p)]
        if not batch:
            continue
        t = time.time()
        try:
            ocr_kraken.run([str(p) for p in batch])
        except Exception as e:  # report and go on; the page stays without text and is retried next run
            print(f"[{time.strftime('%H:%M:%S')}] worker {wid}: FAILED pp. {batch[0]}-{batch[-1]}: {e}", flush=True)
            continue
        done[0] += len(batch)
        print(f"[{time.strftime('%H:%M:%S')}] worker {wid}: pp. {batch[0]}-{batch[-1]} in {time.time() - t:.0f} s; "
              f"{done[0]}/{total} done", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--workers", type=int, default=3)
    a.add_argument("--first", type=int, default=1)
    a.add_argument("--last", type=int, default=598)
    a = a.parse_args()
    todo = [p for p in range(a.first, a.last + 1) if not (TEXT / f"p{p:03d}.txt").exists()]
    print(f"{len(todo)} pages to read with {a.workers} workers", flush=True)
    done = [0]
    with ThreadPoolExecutor(a.workers) as ex:
        for w in range(a.workers):
            ex.submit(worker, todo[w::a.workers], w, len(todo), done)
    left = [p for p in range(a.first, a.last + 1) if not (TEXT / f"p{p:03d}.txt").exists()]
    print(f"finished: {len(todo) - len(left)} read, {len(left)} still without text {left[:20]}", flush=True)


if __name__ == "__main__":
    main()
