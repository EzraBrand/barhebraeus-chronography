"""Fine-tuning, step 2 (ALTO version, 20-Nov-2026): corrected copies of the ALTO files of ft_alto.py.
  uv run ft_build_alto.py    -> data/ft/alto_gt/{train,eval}/pNNN.xml, data/ft/corrections.tsv, data/ft/{train,eval}.txt
Training from ALTO lets ketos cut each line along its polygon, as Kraken does when it reads (rectangular crops of
ft_build.py gave the base model only 17% accuracy; its own ALTO gives 100%). Corrections, as in ft_build.py: the lost
first letter (data/qa/line_start.tsv) and the confirmed corrections (data/qa/confirmed.tsv); the full word in its most
frequent vocalised form in the corpus. The String CONTENT is in visual order (the model's), so the corrected word is
written as logical(word) (ocr_kraken.logical is its own inverse). The line's logical first word is its last String.
20% of the pages (with their corrections) are held out for evaluation.
"""
import csv
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from ocr_kraken import logical
from qa_words import cons

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
ALTO = ROOT / "data" / "ft" / "alto"
GT = ROOT / "data" / "ft" / "alto_gt"
PUNCT = re.compile(r"[^ܐ-ݏ̀-ͯ]+$")


def main() -> None:
    forms = defaultdict(Counter)
    for t in (ROOT / "data" / "text").glob("p*.txt"):
        for tok in t.read_text(encoding="utf-8").split():
            base = PUNCT.sub("", tok)
            if cons(base):
                forms[cons(base)][base] += 1
    fixes = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "data" / "qa" / "line_start.tsv", encoding="utf-8"), delimiter="\t"):
        fixes[int(r["page"])].append((int(r["line"]), r["read"], r["likely"]))
    conf = ROOT / "data" / "qa" / "confirmed.tsv"
    if conf.exists():
        for r in csv.DictReader(open(conf, encoding="utf-8"), delimiter="\t"):
            fixes[int(r["bedjan_page"])].append((None, r["bedjan"], r["bk"]))

    pages = sorted(int(x.stem[1:]) for x in ALTO.glob("p*.xml"))
    random.seed(11)
    ev = set(random.sample(pages, max(1, len(pages) // 5)))
    log, n_fixed = [], Counter()
    for split in ("train", "eval"):
        (GT / split).mkdir(parents=True, exist_ok=True)
        for f in (GT / split).glob("*.xml"):
            f.unlink()
    for p in pages:
        tree = ET.parse(ALTO / f"p{p:03d}.xml")
        root = tree.getroot()
        ns = root.tag.split("}")[0][1:]
        ET.register_namespace("", ns)
        text_lines = [ln for ln in (ROOT / "data" / "text" / f"p{p:03d}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
        for tl in root.iter(f"{{{ns}}}TextLine"):
            strings = tl.findall(f"{{{ns}}}String")
            if not strings:
                continue
            vis = " ".join(s.get("CONTENT", "") for s in strings)
            k = next((i for i, t in enumerate(text_lines, 1) if t == logical(vis)), None)
            for line_no, read, right in fixes.get(p, []):
                if line_no is not None and line_no != k:
                    continue
                # the String whose logical word has the consonants `read`; for a line start, only the last String
                cands = [strings[-1]] if line_no is not None else strings
                for s in cands:
                    word = logical(s.get("CONTENT", ""))
                    core = PUNCT.sub("", word)
                    if cons(core) == read:
                        voc = forms[right].most_common(1)[0][0] if forms[right] else right
                        new = voc + word[len(core):]
                        s.set("CONTENT", logical(new))
                        log.append((p, k, word, new, "eval" if p in ev else "train"))
                        n_fixed["eval" if p in ev else "train"] += 1
                        break
        tree.write(GT / ("eval" if p in ev else "train") / f"p{p:03d}.xml", encoding="utf-8", xml_declaration=True)
    for split in ("train", "eval"):
        (ROOT / "data" / "ft" / f"{split}.txt").write_text(
            "\n".join(str(x.resolve()) for x in sorted((GT / split).glob("*.xml"))), encoding="utf-8")
    with open(ROOT / "data" / "ft" / "corrections.tsv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerows([("page", "line", "read", "corrected", "split")] + log)
    print(f"{len(pages)} pages: {len(pages) - len(ev)} train ({n_fixed['train']} corrected words), "
          f"{len(ev)} eval ({n_fixed['eval']} corrected words)")


if __name__ == "__main__":
    main()
