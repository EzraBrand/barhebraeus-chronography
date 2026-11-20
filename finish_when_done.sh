#!/bin/bash
# Wait for ocr_book.py to finish (its log says "finished"), then rebuild the site, commit and push.
cd "$(dirname "$0")"
LOG=$1
until grep -q "^finished" "$LOG"; do sleep 60; done
uv run build_site.py >> "$LOG" 2>&1
n=$(ls data/text | wc -l)
git add -A && git commit -q -m "OCR of the whole book: $n of 599 pages ($(grep '^finished' "$LOG"))

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q >> "$LOG" 2>&1
echo "PUSHED $(date +%H:%M)" >> "$LOG"
