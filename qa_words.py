"""Free checks of the OCR from the text itself (20-Nov-2026). Words are compared on their consonants (vowel points and
seyame removed, ܤ = ܣ). The first line of a page (the running header) is left out.
  uv run qa_words.py            -> data/qa/suspects.tsv, data/qa/line_start.tsv and a summary
1. Line start: Kraken often drops the first (rightmost) letter of a printed line. For each line's first word, look for a
   frequent word that is the same word with one letter in front ("lost letter"); the same test on words in the middle of
   lines gives the base rate.
2. Suspects: a word seen once whose neighbour at edit distance 1 is seen 10 times or more (ܓܪܒܚܐ / ܓܪܒܝܐ).
Report only: a rare word can be right (a name, a rare form); read a sample on the scan before any rule.
"""
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
TEXT = ROOT / "data" / "text"
OUT = ROOT / "data" / "qa"
LETTERS = "ܐܒܓܕܗܘܙܚܛܝܟܠܡܢܣܥܦܨܩܪܫܬ"


def cons(w: str) -> str:
    w = unicodedata.normalize("NFD", w).replace("ܤ", "ܣ")
    return "".join(c for c in w if "ܐ" <= c <= "ܯ")


def pages():
    for p in sorted(TEXT.glob("p*.txt")):
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        yield int(p.stem[1:]), lines[1:]  # line 1 = the running header


def neighbours(w: str):
    for i in range(len(w) + 1):  # one letter added
        for c in LETTERS:
            yield w[:i] + c + w[i:]
    for i in range(len(w)):  # one letter changed or dropped
        yield w[:i] + w[i + 1:]
        for c in LETTERS:
            if c != w[i]:
                yield w[:i] + c + w[i + 1:]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    freq = Counter()
    places = defaultdict(list)
    first, middle = [], []
    for p, lines in pages():
        for k, ln in enumerate(lines, 2):
            ws = [cons(w) for w in ln.split()]
            ws = [w for w in ws if w]
            for j, w in enumerate(ws):
                freq[w] += 1
                places[w].append((p, k))
                (first if j == 0 else middle).append((w, p, k))

    def lost_letter(w):  # a frequent word = one letter + w
        best = max(((freq[c + w], c + w) for c in LETTERS), default=(0, ""))
        return best if best[0] >= 5 and freq[w] <= 2 else None

    rows, hit_first = [], 0
    for w, p, k in first:
        r = lost_letter(w)
        if r:
            hit_first += 1
            rows.append((p, k, w, r[1], r[0]))
    hit_mid = sum(1 for w, _, _ in middle if lost_letter(w))
    with open(OUT / "line_start.tsv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerows([("page", "line", "read", "likely", "count of likely")] + rows)

    sus = []
    for w, n in freq.items():
        if n != 1 or len(w) < 3:
            continue
        cands = sorted(((freq[x], x) for x in set(neighbours(w)) if freq[x] >= 10), reverse=True)
        if cands:
            p, k = places[w][0]
            sus.append((p, k, w, cands[0][1], cands[0][0]))
    sus.sort()
    with open(OUT / "suspects.tsv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerows([("page", "line", "read", "neighbour", "neighbour count")] + sus)

    nw = sum(freq.values())
    print(f"{len(list(TEXT.glob('p*.txt')))} pages, {nw} words, {len(freq)} distinct (consonants)")
    print(f"line start: {hit_first} of {len(first)} first words ({hit_first / max(len(first), 1):.1%}) look like a frequent "
          f"word without its first letter; in the middle of lines {hit_mid} of {len(middle)} ({hit_mid / max(len(middle), 1):.2%})")
    print(f"suspects: {len(sus)} words seen once with a frequent neighbour at one letter -> data/qa/suspects.tsv")


if __name__ == "__main__":
    main()
