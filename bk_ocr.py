"""OCR of the Bruns-Kirsch edition (Leipzig 1789, Serto type) for the cross-edition check.
  uv run bk_ocr.py 30 80 ...        # data/bruns_kirsch/bk_pNNN.jpg -> data/bruns_kirsch/text/pNNN.txt
Models: Qoruyo print segmentation and the Qoruyo Serto recognition model (serto_print_best_02.mlmodel). The output is in
visual order; ocr_kraken.logical() turns it into logical order, as for Bedjan."""
import os
import subprocess
import sys
from pathlib import Path

from ocr_kraken import KRAKEN, SEG, K, logical

ROOT = Path(__file__).resolve().parent
BK = ROOT / "data" / "bruns_kirsch"
REC = K / "serto_print_best_02.mlmodel"


def run(pages: list[str]) -> None:
    (BK / "raw").mkdir(exist_ok=True)
    (BK / "text").mkdir(exist_ok=True)
    args = []
    for p in pages:
        args += ["-i", str(BK / f"bk_p{int(p):03d}.jpg"), str(BK / "raw" / f"p{int(p):03d}.raw.txt")]
    subprocess.run([str(KRAKEN), *args, "segment", "-bl", "-i", str(SEG), "ocr", "-m", str(REC)], check=True,
                   env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    for p in pages:
        raw = (BK / "raw" / f"p{int(p):03d}.raw.txt").read_text(encoding="utf-8")
        (BK / "text" / f"p{int(p):03d}.txt").write_text("\n".join(logical(x) for x in raw.splitlines()) + "\n", encoding="utf-8")
        print(p, len(raw.splitlines()), "lines", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run(sys.argv[1:])
