"""OCR of Bedjan's Chronicon Syriacum (1890) with Kraken and Beth Mardutho's Qoruyo models (pilot, 20-Nov-2026).
  uv run ocr_kraken.py PAGE [PAGE ...]      # data/raw/bedjan_pNNN.jpg -> data/kraken/pNNN.raw.txt + data/text/pNNN.txt
Kraken (7.1.1) runs from its own venv (../syriac-ocr/.venv, Python 3.12; see README). Models (CC-BY 4.0, Zenodo):
  segmentation  syr_print_seg03_91.mlmodel   (Qoruyo, printed texts, record 17406626)
  recognition   SyrEastSyr_01_18.mlmodel     (Qoruyo, printed East Syriac, record 17406690): Bedjan's type is East Syriac
The models were trained on text in visual order (left to right), and the vowel marks come before their letter in the
output: one reversal of the whole line gives logical order for the Syriac. Digits and Latin are then reversed back and
brackets swapped (logical()).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
K = ROOT.parent / "syriac-ocr"
KRAKEN = K / ".venv" / "Scripts" / "kraken.exe"
SEG = K / "syr_print_seg03_91.mlmodel"
REC = K / "SyrEastSyr_01_18.mlmodel"
LTR_RUN = re.compile(r"[0-9A-Za-zÀ-ɏ]+(?:[.,:\-][0-9A-Za-zÀ-ɏ]+)*")
MIRROR = str.maketrans("()[]{}<>", ")(][}{><")


def logical(line: str) -> str:
    """visual-order Kraken output -> logical order"""
    t = line[::-1].translate(MIRROR)
    return LTR_RUN.sub(lambda m: m.group(0)[::-1], t)


def run(pages: list[str]) -> None:
    (ROOT / "data" / "kraken").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "text").mkdir(parents=True, exist_ok=True)
    args = []
    for p in pages:
        args += ["-i", str(ROOT / "data" / "raw" / f"bedjan_p{int(p):03d}.jpg"), str(ROOT / "data" / "kraken" / f"p{int(p):03d}.raw.txt")]
    subprocess.run([str(KRAKEN), *args, "segment", "-bl", "-i", str(SEG), "ocr", "-m", str(REC)], check=True,
                   env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    for p in pages:
        raw = (ROOT / "data" / "kraken" / f"p{int(p):03d}.raw.txt").read_text(encoding="utf-8")
        out = "\n".join(logical(ln) for ln in raw.splitlines())
        (ROOT / "data" / "text" / f"p{int(p):03d}.txt").write_text(out + "\n", encoding="utf-8")
        print(p, len(raw.splitlines()), "lines", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run(sys.argv[1:])
