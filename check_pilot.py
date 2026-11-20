"""Pilot check: Kraken's reading of Bedjan (1890, East Syriac type) against an independent text of the same passage.
The reference is the year AG 1095 (AD 784, the locusts) as transcribed on 20-Nov-2026 for the Bochart project from two
other prints in Serto type (Rosenmüller's Bochart, vol. 3 p. 283, and Bruns-Kirsch 1789, p. 134; Kraken on both,
reconciled by hand with Rosenmüller's Latin). Two words of that reconciliation (ܘܡܣܒܟ, ܘܠܓ̈ܐ) were then corrected
from Bedjan's vocalised text, so for those two the check is not independent. Compared on consonants only (no vowel points, no seyame).
  uv run check_pilot.py
"""
import sys
import unicodedata
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Levenshtein

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
REF = ("ܒܫܢܬ ܐܨܗ ܕܝ̈ܘܢܝܐ ܐܬܐ ܩܡܨܐ ܦܪܚܐ ܘܚܒܠ ܙܪ̈ܥܐ ܘܐܪܡܝ ܙܪܥܐ ܘܢܦܩ. ܘܡܣܒܟ ܗܘܐ ܘܣܠܩ ܒܫܘܪ̈ܐ ܘܐܣ̈ܐ. ܘܥܐܠ "
       "ܡܢ ܟܘ̈ܐ ܘܬܪ̈ܥܐ ܠܒ̈ܬܐ. ܘܐܬܡܠܝܘ ܡܢܗ ܐܦ ܓܪ̈ܒܐ ܕܡ̈ܝܐ ܘܬܫܘܝ̈ܬܐ ܘܦܬܘܪ̈ܐ ܘܠܓ̈ܐ. ܘܟܕ ܡܢ ܦܢܝܬ ܬܝܡܢܐ "
       "ܥܐܠ ܗܘܐ ܠܒܝܬܐ ܡܢ ܓܒܐ ܓܪܒܝܝܐ ܢܦܩ ܗܘܐ. ܘܐܟܠ ܥܡ ܥܣܒܐ ܘܐܝܠ̈ܢܐ. ܐܦ ܡܐ̈ܢܐ ܕܥܡܪܐ ܘܢܚ̈ܬܐ ܕܒ̈ܢܝܢܫܐ. "
       "ܘܟܕ ܓܡܪ ܠܟܠܗ ܦܢܝܬܐ ܕܐܘܪܗܝ ܘܣܪܘܓ ܥܒܪ ܠܡܥܪܒܐ.")


def cons(w: str) -> str:
    w = unicodedata.normalize("NFD", w)
    w = w.replace("ܤ", "ܣ")  # ܤ (the East Syriac form of semkath in Bedjan's type) = ܣ
    return "".join(c for c in w if "ܐ" <= c <= "ܯ" or "ݍ" <= c <= "ݏ")


def words(text: str) -> list[str]:
    return [c for c in (cons(w) for w in text.split()) if c]


def align(a, b):
    n, m = len(a), len(b)
    D = np.zeros((n + 1, m + 1))
    D[:, 0] = np.arange(n + 1)
    D[0, :] = 0  # the reference may start anywhere in b
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = Levenshtein.normalized_distance(a[i - 1], b[j - 1])
            D[i, j] = min(D[i - 1, j] + 1, D[i, j - 1] + 1, D[i - 1, j - 1] + s)
    j = int(np.argmin(D[n, :]))  # ... and end anywhere
    i, pairs = n, []
    while i > 0 and j > 0:
        s = Levenshtein.normalized_distance(a[i - 1], b[j - 1])
        if D[i, j] == D[i - 1, j - 1] + s:
            pairs.append((a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif D[i, j] == D[i - 1, j] + 1:
            pairs.append((a[i - 1], "")); i -= 1
        else:
            pairs.append(("", b[j - 1])); j -= 1
    while i > 0:
        pairs.append((a[i - 1], "")); i -= 1
    return pairs[::-1]


def main() -> None:
    ref = words(REF)
    pages = sorted((ROOT / "data" / "text").glob("p*.txt"))
    bed = []
    for p in pages:
        bed += words(p.read_text(encoding="utf-8"))
    pairs = align(ref, bed)
    same = sum(1 for x, y in pairs if x and x == y)
    near = sum(1 for x, y in pairs if x and y and Levenshtein.distance(x, y) <= 1)
    chars = sum(len(x) for x, _ in pairs if x)
    errs = sum(Levenshtein.distance(x, y) for x, y in pairs if x)
    print(f"reference {len(ref)} words; Bedjan pp. {pages[0].stem[1:]}-{pages[-1].stem[1:]}, {len(bed)} words read by Kraken")
    print(f"same word: {same} ({same / len(ref):.0%}); within one letter: {near} ({near / len(ref):.0%}); "
          f"character difference {errs}/{chars} ({errs / chars:.1%}), counting real variants between the editions as errors")
    for x, y in pairs:
        if x != y:
            print(f"  ref {x or '-':14} Bedjan/Kraken {y or '-'}")


if __name__ == "__main__":
    main()
