# barhebraeus-chronography

Pilot (20-Nov-2026): OCR of Barhebraeus' *Chronography* (the first, secular part of his history, the *Chronicon
Syriacum*) in the edition of Paul Bedjan, *Gregorii Barhebraei Chronicon Syriacum e codd. mss. emendatum ac punctis
vocalibus adnotationibusque locupletatum* (Paris: Maisonneuve, 1890; printed by Drugulin, Leipzig). As far as we found,
no Unicode text of this edition is online: the archive.org OCR of the BYU scan is not in Syriac letters.

The method comes from the Bochart project ([bochart-hierozoicon](https://github.com/EzraBrand/bochart-hierozoicon),
`SYRIAC.md`): vision LLMs cannot read a long Syriac text, but Kraken with Beth Mardutho's Qoruyo models can.

**Read it:** https://ezrabrand.github.io/barhebraeus-chronography/ (each page line by line: the Syriac as Kraken
read it, and the same words in Hebrew letters; `uv run build_site.py` writes `docs/`). The Hebrew letters come from a
fixed table (the one of the Bochart project: one letter per consonant, final forms at word end, vowels left out; ܤ = ס).

## Source

- Scan: University of Toronto (Robarts), archive.org item
  [`ketabademadatbez00barhuoft`](https://archive.org/details/ketabademadatbez00barhuoft), 400 ppi, 620 leaves, no
  licence restriction. Bedjan's pages run from the back of the scan: **printed page = 605 − leaf**.
  A second scan (BYU, 600 ppi, item `Bedjan1890GregoriiBarhebraeiChroniconSyriacum`) carries a CC BY-NC-ND licence
  for the scan; not used.
- Type: **East Syriac**, fully vocalised (not Serto, as in the 1789 Bruns-Kirsch edition).
- The page images are not stored in this repository (`data/raw/` is gitignored). They were fetched through the browser
  (`b64save.py`): the leaf's JPEG is
  `https://archive.org/download/ketabademadatbez00barhuoft/ketabademadatbez00barhuoft_jp2.zip/ketabademadatbez00barhuoft_jp2%2Fketabademadatbez00barhuoft_LLLL.jp2&ext=jpg&reduce=0&quality=95`
  (2098 × 3308 px).

## OCR

`uv run ocr_kraken.py 120 121 ...` runs Kraken 7.1.1 from a separate Python 3.12 environment
(`../syriac-ocr/.venv`) with two Qoruyo models (CC-BY 4.0, Zenodo):

| step | model | Zenodo record |
|---|---|---|
| segmentation (baselines) | `syr_print_seg03_91.mlmodel` | 17406626 |
| recognition, East Syriac print | `SyrEastSyr_01_18.mlmodel` | 17406690 |

Kraken's raw output is in visual order (`data/kraken/pNNN.raw.txt`); `ocr_kraken.logical()` turns each line into
logical order (one reversal of the line, then digits and Latin turned back and brackets swapped) and writes
`data/text/pNNN.txt`. About 35-90 seconds a page on the laptop's CPU, free.

## Pilot result: pp. 120-129

The 10 pages give 2,365 words. The check (`uv run check_pilot.py`) is the year AG 1095 (AD 784, the plague of locusts,
Bedjan p. 128), which was transcribed earlier the same day from two other prints in another script (Rosenmüller's
Bochart, vol. 3 p. 283, and Bruns-Kirsch 1789, p. 134, both Serto, read with Kraken's Serto model and reconciled by
hand). Compared on consonants (vowel points and seyame removed; ܤ counted as ܣ):

- 58 words; **55 the same (95%)** before the comparison was used to correct the reference;
- of the 3 differences, 2 were errors in the reference, not in Bedjan's OCR: Bedjan's vowels show ܘܲܡܤܲܒܸܟ݂ (read ܘܡܫܬܟܚ
  by hand from the Serto prints, where Kraken had read ܘܡܣܒܟ in both) and ܘܠܲܓܹ̈ܐ (read ܘܠܓ̈ܢܐ); both were corrected in
  the Bochart project;
- 1 is a Kraken error in Bedjan: ܓܪܒܚܐ for ܓܪܒܝܐ (north).

Other errors seen on a read-through of p. 128: the year digits (Bedjan's "1095" read as 1025), a final punctuation
mark read as ؟. The vowel points have not been checked yet.

## Reader layout (20-Nov-2026)

Each page is split at its punctuation (`.` and `:`; `segments.py`), not by printed line: one row per phrase, Hebrew letters on
the left, the Syriac on the right (on a phone: Syriac first). Bedjan's notes (lines that begin with a note number) come
at the end. P. 1 also has an English translation per segment (`data/translation/p001.json`, by Claude from the OCR
text, God addressed with modern You/Your, not checked by a Syriacist): `build_site.py` adds an English column to any page
that has such a file.

## To do (later, not now)

- **English translation of the other pages**, segment by segment, in the format of `data/translation/p001.json` (one entry
  per segment of `segments.py`, `{OCR: ...}` for doubtful readings, modern You/Your for God). Check a sample against Budge's
  translation (1932) first. The OCR fixes below come before it, because a segment split changes when the text changes.
- **The first letter of a line**: Kraken often drops the rightmost letter of a printed line (p. 1: ܕ for ܚܕ, ܒ̈ܢܐ for ܙܒ̈ܢܐ,
  ܕܝܢܬܐ for ܡܕܝܢܬܐ). Try a wider line polygon at the right edge (segmentation padding) and measure on p. 1 and p. 128.
- **Page header and page number**: on the uncropped JPEG 2000 images the facing page shows through above the header
  (p. 30: the header read as the book title, the page number as "86"). Drop the first line (or two) of each page before
  the split, after a check on a sample.
- **Year digits** (p. 128: "1095" read as "1025") and the vowel points: not checked yet.

## Next steps

1. **Scale.** 600 pages at about one minute a page is about 10 hours of CPU: run in the background, 2-3 processes,
   resumable (skip pages whose `data/text/pNNN.txt` exists). The download of 600 leaves (about 1.4 GB) through the
   browser is slow in batches of 5: better a download command run by the owner (the archive.org jp2 zip, 416 MB).
2. **A second check page**: another passage that has an independent text (Bruns-Kirsch 1789 has the whole chronicle in
   Serto: the two editions can be compared page by page, which also measures Kraken's Serto reading).
3. **Layout**: the page header, Bedjan's notes at the foot and his marginal numbers come out as text lines; mark them
   (line position) before the text is joined.
4. **Translation**: Budge's English translation (1932) exists; an English side-by-side is not needed for every page,
   but a site like Bochart's (Syriac with a parallel English) would make the text searchable.
