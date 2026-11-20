"""Cross-edition check: Kraken's Bedjan (1890, East Syriac) against Kraken's Bruns-Kirsch (1789, Serto) for the same
passages. The two editions differ in script, line breaks, page breaks and some readings, so a word that both readings
agree on is right with high probability (two independent prints, two models), and a disagreement is either an OCR error
in one of them or a real variant. Consonants only (vowels and seyame removed, ܤ = ܣ).
  uv run cross_check.py        -> data/qa/cross_check.tsv and a summary
Each disagreement is classified by the frequency of the two forms in Bedjan's whole OCR text:
  bedjan?   the Bedjan form is rare (<= 2) and the 1789 form is frequent (>= 5): probably an OCR error in Bedjan
  bk?       the reverse: probably an OCR error in the 1789 reading
  variant   both are frequent: a real difference between the editions, or a common-word confusion
  unclear   both rare
"""
import csv
import sys
from collections import Counter
from pathlib import Path

from check_pilot import align
from qa_words import cons

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
BKT = ROOT / "data" / "bruns_kirsch" / "text"
BED = ROOT / "data" / "text"
OUT = ROOT / "data" / "qa"


def words_of(path: Path, skip_header: bool = True) -> list[str]:
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if skip_header:
        lines = lines[1:]
    return [c for c in (cons(w) for ln in lines for w in ln.split()) if c]


def main() -> None:
    bed = {int(p.stem[1:]): words_of(p) for p in sorted(BED.glob("p*.txt"))}
    freq = Counter(w for ws in bed.values() for w in ws)
    tri = {p: set(zip(ws, ws[1:], ws[2:])) for p, ws in bed.items()}
    rows, tot = [], Counter()
    for bkp in sorted(BKT.glob("p*.txt")):
        a = words_of(bkp)
        t = set(zip(a, a[1:], a[2:]))
        best = max(tri, key=lambda p: len(t & tri[p]))
        if len(t & tri[best]) < 3:
            print(f"BK {bkp.stem}: no Bedjan page found (Bedjan pages so far: {len(bed)})")
            continue
        window = bed.get(best - 1, []) + bed[best] + bed.get(best + 1, [])
        pairs = align(a, window)
        same = sum(1 for x, y in pairs if x and x == y)
        near = sum(1 for x, y in pairs if x and y and x != y and len(x) > 1 and abs(len(x) - len(y)) <= 1)
        tot["words"] += len(a)
        tot["same"] += same
        print(f"BK {bkp.stem} ~ Bedjan p. {best}: {len(a)} words, {same} the same ({same / len(a):.0%})")
        for x, y in pairs:
            if x and y and x != y:
                fx, fy = freq[x], freq[y]
                kind = ("bedjan?" if fy <= 2 and fx >= 5 else "bk?" if fx <= 2 and fy >= 5
                        else "variant" if fx >= 5 and fy >= 5 else "unclear")
                tot[kind] += 1
                rows.append((bkp.stem, best, x, y, fx, fy, kind))
    # confirmed corrections: the 1789 word is one letter from the Bedjan word, frequent in Bedjan, and the Bedjan form is rare
    from rapidfuzz.distance import Levenshtein
    conf = [r for r in rows if Levenshtein.distance(r[2], r[3]) == 1 and r[4] >= 5 and r[5] <= 2]
    with open(OUT / "confirmed.tsv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="	").writerows([("bk_page", "bedjan_page", "bk", "bedjan", "freq_bk_form", "freq_bedjan_form")] +
                                                [r[:6] for r in conf])
    print(f"confirmed Bedjan corrections (one letter, the 1789 form frequent, the Bedjan form rare): {len(conf)} -> data/qa/confirmed.tsv")
    OUT.mkdir(exist_ok=True)
    with open(OUT / "cross_check.tsv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerows([("bk_page", "bedjan_page", "bk", "bedjan", "freq_bk_form", "freq_bedjan_form", "kind")] + rows)
    if tot["words"]:
        print(f"total: {tot['words']} words of the 1789 pages, {tot['same']} the same in Bedjan ({tot['same'] / tot['words']:.0%}); "
              f"disagreements: bedjan? {tot['bedjan?']}, bk? {tot['bk?']}, variant {tot['variant']}, unclear {tot['unclear']}")


if __name__ == "__main__":
    main()
