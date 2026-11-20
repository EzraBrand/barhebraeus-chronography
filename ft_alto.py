"""Fine-tuning, step 1: Kraken with ALTO output (line boxes and text) for the pages that have flagged lines.
  uv run ft_alto.py [--workers 3]      # pages from data/qa/line_start.tsv and confirmed.tsv -> data/ft/alto/pNNN.xml
Same models and settings as the book run (ocr_kraken.py), so the lines and their text are those of data/kraken/*.raw.txt.
"""
import argparse
import csv
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ocr_kraken import KRAKEN, REC, SEG

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "ft" / "alto"


def flagged_pages() -> list[int]:
    pages = {int(r["page"]) for r in csv.DictReader(open(ROOT / "data" / "qa" / "line_start.tsv", encoding="utf-8"), delimiter="\t")}
    conf = ROOT / "data" / "qa" / "confirmed.tsv"
    if conf.exists():
        pages |= {int(r["bedjan_page"]) for r in csv.DictReader(open(conf, encoding="utf-8"), delimiter="\t")}
    return sorted(pages)


def run(batch: list[int]) -> None:
    args = []
    for p in batch:
        args += ["-i", str(ROOT / "data" / "raw" / f"bedjan_p{p:03d}.jpg"), str(OUT / f"p{p:03d}.xml")]
    subprocess.run([str(KRAKEN), "-a", *args, "segment", "-bl", "-i", str(SEG), "ocr", "-m", str(REC)], check=False,
                   env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}, capture_output=True)
    print(f"pp. {batch[0]}-{batch[-1]} done", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    a = argparse.ArgumentParser()
    a.add_argument("--workers", type=int, default=3)
    a = a.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [p for p in flagged_pages() if not (OUT / f"p{p:03d}.xml").exists()]
    print(len(todo), "pages", flush=True)
    batches = [todo[i:i + 8] for i in range(0, len(todo), 8)]
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(run, batches))
    print("ALTO done:", len(list(OUT.glob("p*.xml"))), "files", flush=True)


if __name__ == "__main__":
    main()
