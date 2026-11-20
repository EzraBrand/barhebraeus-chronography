"""Fine-tuning, step 2: training lines (image + .gt.txt) from the ALTO files of ft_alto.py.
  uv run ft_build.py     -> data/ft/lines/{train,eval}/NNNN.png + .gt.txt, data/ft/corrections.tsv, a summary
Corrected lines: the lost first letter (data/qa/line_start.tsv: the line's first word plus one letter in front is a
frequent word) and the confirmed corrections of the cross-edition check (data/qa/confirmed.tsv). The full word is put
in its most frequent vocalised form in the corpus. Clean lines: other lines of the same pages whose words are all
frequent (>= 3), as they are. The text is in the visual order that the model emits (ocr_kraken.logical is its own
inverse), so training uses --no-reorder. 20% of the corrected lines are held out for evaluation (eval/), with 10% of the
clean lines.
"""
import csv
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from ocr_kraken import logical
from qa_words import cons

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
ALTO = ROOT / "data" / "ft" / "alto"
LINES = ROOT / "data" / "ft" / "lines"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
PUNCT = re.compile(r"[^ܐ-ݏ̀-ͯ]+$")


def alto_lines(p: int):
    root = ET.parse(ALTO / f"p{p:03d}.xml").getroot()
    ns = {"a": root.tag.split("}")[0][1:]} if root.tag.startswith("{") else {}
    q = (lambda t: f"a:{t}") if ns else (lambda t: t)
    for tl in root.iter(f"{{{ns['a']}}}TextLine" if ns else "TextLine"):
        words = [s.get("CONTENT", "") for s in tl.findall(q("String"), ns)]
        box = tuple(int(float(tl.get(k))) for k in ("HPOS", "VPOS", "WIDTH", "HEIGHT"))
        yield " ".join(words), box


def main() -> None:
    # vocalised forms of each consonant word in the whole corpus
    forms = defaultdict(Counter)
    freq = Counter()
    for t in (ROOT / "data" / "text").glob("p*.txt"):
        for tok in t.read_text(encoding="utf-8").split():
            base = PUNCT.sub("", tok)
            c = cons(base)
            if c:
                forms[c][base] += 1
                freq[c] += 1
    fixes = defaultdict(list)  # page -> (line number or None, read cons, right cons)
    for r in csv.DictReader(open(ROOT / "data" / "qa" / "line_start.tsv", encoding="utf-8"), delimiter="\t"):
        fixes[int(r["page"])].append((int(r["line"]), r["read"], r["likely"]))
    conf = ROOT / "data" / "qa" / "confirmed.tsv"
    if conf.exists():
        for r in csv.DictReader(open(conf, encoding="utf-8"), delimiter="\t"):
            fixes[int(r["bedjan_page"])].append((None, r["bedjan"], r["bk"]))

    corrected, clean, log = [], [], []
    for xml in sorted(ALTO.glob("p*.xml")):
        p = int(xml.stem[1:])
        img = Image.open(ROOT / "data" / "raw" / f"bedjan_p{p:03d}.jpg").convert("L")
        text_lines = [ln for ln in (ROOT / "data" / "text" / f"p{p:03d}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
        for visual, (x, y, w, h) in alto_lines(p):
            log_line = logical(visual)
            if not log_line.strip():
                continue
            k = next((i for i, t in enumerate(text_lines, 1) if t == log_line), None)
            toks = log_line.split()
            new = list(toks)
            for line_no, read, right in fixes.get(p, []):
                if line_no is not None and line_no != k:
                    continue
                for j, tok in enumerate(new):
                    if cons(PUNCT.sub("", tok)) == read and (line_no is None or j == 0):
                        voc = forms[right].most_common(1)[0][0] if forms[right] else right
                        new[j] = voc + tok[len(PUNCT.sub("", tok)):]
                        log.append((p, k, tok, new[j]))
                        break
            # crop: the line box, with a margin; more on the right, where the first letter is lost
            crop = img.crop((max(x - 16, 0), max(y - 10, 0), min(x + w + 48, img.width), min(y + h + 10, img.height)))
            item = (crop, logical(" ".join(new)))
            if new != toks:
                corrected.append(item)
            elif all(freq[cons(PUNCT.sub("", t))] >= 3 for t in toks if cons(t)):
                clean.append(item)
    random.seed(7)
    random.shuffle(corrected)
    random.shuffle(clean)
    ne, nc = max(1, len(corrected) // 5), len(clean) // 10
    sets = {"eval": corrected[:ne] + clean[:nc], "train": corrected[ne:] + clean[nc:]}
    for name, items in sets.items():
        d = LINES / name
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*"):
            f.unlink()
        for i, (im, gt) in enumerate(items):
            im.save(d / f"{i:04d}.png")
            (d / f"{i:04d}.gt.txt").write_text(gt, encoding="utf-8")
    (LINES / "eval_corrected.txt").write_text("\n".join(f"{i:04d}" for i in range(ne)), encoding="utf-8")
    with open(ROOT / "data" / "ft" / "corrections.tsv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerows([("page", "line", "read", "corrected")] + log)
    print(f"{len(corrected)} corrected lines ({ne} held out), {len(clean)} clean lines ({nc} held out); "
          f"train {len(sets['train'])}, eval {len(sets['eval'])}")


if __name__ == "__main__":
    main()
