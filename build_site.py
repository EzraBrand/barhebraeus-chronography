"""Build the reader (GitHub Pages, docs/): each page of Bedjan's text line by line, the Syriac (as Kraken read it) and
a transliteration into Hebrew letters, with a link to the scan.
  uv run build_site.py
The transliteration is the deterministic table of the Bochart project (bochart-hierozoicon/translate.py,
syriac_to_hebrew): one Hebrew letter per Syriac consonant, final forms at the end of a word, vowel points and other
marks left out. Added here: ܤ (final semkath of the East Syriac type) = ס. Digits and punctuation are kept.
"""
import html
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
TEXT = ROOT / "data" / "text"
DOCS = ROOT / "docs"
ITEM = "ketabademadatbez00barhuoft"
SYRIAC_TO_HEBREW = dict(zip("ܐܒܓܕܗܘܙܚܛܝܟܠܡܢܣܥܦܨܩܪܫܬܤ", "אבגדהוזחטיכלמנסעפצקרשתס"))
FINALS = dict(zip("כמנפצ", "ךםןףץ"))
MARK = re.compile(r"[̀-ͯܰ-ܑ݊]")  # vowel points, seyame and other marks (and superscript alaph)


def to_hebrew(line: str) -> str:
    out = []
    for w in MARK.sub("", line).split():
        h = "".join(SYRIAC_TO_HEBREW.get(c, c) for c in w)
        # final form for the last Hebrew letter of the word (before any trailing punctuation)
        m = re.search(r"([כמנפצ])([^א-ת]*)$", h)
        if m and re.search(r"[א-ת]", h[:m.start()]):
            h = h[:m.start()] + FINALS[m.group(1)] + m.group(2)
        out.append(h)
    return " ".join(out)


def leaf(page: int) -> int:
    return 605 - page  # Bedjan's pages run from the back of the scan


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1b18;--muted:#6b665e;--line:#e4e0d8;--accent:#7a3b12;--card:#fff}
@media (prefers-color-scheme: dark){:root{--bg:#161513;--fg:#ece8e1;--muted:#a49d92;--line:#33302b;--accent:#e2a06b;--card:#1e1c19}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 Georgia,"Times New Roman",serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 .3rem} h2{font-size:1.2rem;margin:2.2rem 0 .6rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
p,li{max-width:46rem} .muted{color:var(--muted)} a{color:var(--accent)}
nav.pages{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0} nav.pages a{padding:.15rem .5rem;border:1px solid var(--line);border-radius:4px;text-decoration:none}
table.lines{width:100%;border-collapse:collapse;background:var(--card)}
table.lines td{border-bottom:1px solid var(--line);padding:.35rem .6rem;vertical-align:top}
td.n{color:var(--muted);font:12px/1.9 system-ui,sans-serif;width:2.5rem;text-align:right}
td.syr{font-family:"Noto Sans Syriac Eastern","Noto Sans Syriac",serif;font-size:1.35rem;line-height:2.1;direction:rtl;text-align:right;width:52%}
td.heb{font-family:"Noto Serif Hebrew","SBL Hebrew",serif;font-size:1.15rem;line-height:2.1;direction:rtl;text-align:right;color:var(--fg)}
tr.hl td{background:rgba(226,160,107,.12)}
.cap{font:13px/1.5 system-ui,sans-serif;color:var(--muted);margin:.3rem 0 .8rem}
@media (max-width:640px){table.lines,table.lines tbody,table.lines tr,table.lines td{display:block;width:100%}td.n{text-align:left;width:auto;padding-bottom:0}td.syr{border-bottom:none}}
"""


def build() -> None:
    DOCS.mkdir(exist_ok=True)
    pages = sorted(int(p.stem[1:]) for p in TEXT.glob("p*.txt"))
    nav = " ".join(f'<a href="#p{p}">{p}</a>' for p in pages)
    parts = []
    for p in pages:
        lines = [ln for ln in (TEXT / f"p{p:03d}.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
        scan = f"https://archive.org/details/{ITEM}/page/n{leaf(p)}/mode/1up"
        rows = []
        for i, ln in enumerate(lines, 1):
            hl = ' class="hl"' if p == 128 and 18 <= i <= 23 else ""
            rows.append(f'<tr{hl}><td class="n">{i}</td><td class="syr" lang="syr">{html.escape(ln)}</td>'
                        f'<td class="heb" lang="he">{html.escape(to_hebrew(ln))}</td></tr>')
        parts.append(f'<h2 id="p{p}">Page {p}</h2><div class="cap">{len(lines)} lines as read by Kraken (the page header is '
                     f'line 1; Bedjan\'s notes are at the foot) · <a href="{scan}">scan, leaf {leaf(p)}</a></div>'
                     f'<table class="lines"><tbody>{"".join(rows)}</tbody></table>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Barhebraeus Chronography</title>
<meta name="description" content="Pilot OCR of Bedjan's edition of Barhebraeus' Chronicon Syriacum (1890), with a transliteration into Hebrew letters.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Syriac+Eastern&family=Noto+Serif+Hebrew&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>
<h1>Barhebraeus, <i>Chronography</i> (ed. Bedjan, 1890)</h1>
<p class="muted">Pilot, 20-Nov-2026 · pp. {pages[0]}–{pages[-1]} of about 600 · machine reading, not proofread</p>
<p>The secular part of the history of Gregory Barhebraeus (1226–1286), in Paul Bedjan's vocalised edition, <i>Gregorii
Barhebraei Chronicon Syriacum</i> (Paris 1890), from the <a href="https://archive.org/details/{ITEM}">University of Toronto scan</a>.
The Syriac was read by <a href="https://github.com/mittagessen/kraken">Kraken</a> with Beth Mardutho's
<a href="https://bethmardutho.org/qoruyo/">Qoruyo</a> models for printed East Syriac (CC BY 4.0). The second column gives the same
words in Hebrew letters, by a fixed letter table (one letter for one consonant; vowels left out), for readers of Hebrew and Aramaic.</p>
<p>How good is it? On p. 128 (highlighted: the plague of locusts of the year 1095 of the Greeks, AD 784) the reading was compared
with a text of the same passage made from two other prints in another script: 55 of 58 words were the same. The vowel points, the
page headers and the notes have not been checked. Method and code:
<a href="https://github.com/EzraBrand/barhebraeus-chronography">github.com/EzraBrand/barhebraeus-chronography</a>.</p>
<nav class="pages">{nav}</nav>
{"".join(parts)}
</main></body></html>"""
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print("wrote docs/index.html,", len(pages), "pages")


if __name__ == "__main__":
    build()
