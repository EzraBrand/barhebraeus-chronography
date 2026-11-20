"""Decode the JSON that the browser step writes (images fetched in the page and returned as base64) into files.
  uv run b64save.py DUMP.json OUTDIR PREFIX [EXT]
The dump is {"key": "<base64>", ...} (or {"b64": ..., "len": ...} for one file); each key becomes OUTDIR/PREFIX_KEY.EXT.
Why a browser: on this machine the shell may not download (organisation policy); the Chrome DevTools page fetches the
archive.org images and writes the dump with evaluate_script(filePath=...)."""
import base64
import json
import re
import sys
from pathlib import Path

dump, out, prefix = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
ext = sys.argv[4] if len(sys.argv) > 4 else "jpg"
out.mkdir(parents=True, exist_ok=True)
d = json.loads(re.search(r"\{.*\}", dump.read_text(encoding="utf-8"), re.S).group())
items = {"": d["b64"]} if "b64" in d else d
for k, v in items.items():
    p = out / (f"{prefix}_{k}.{ext}" if k else f"{prefix}.{ext}")
    p.write_bytes(base64.b64decode(v))
    print(p, p.stat().st_size)
dump.unlink()
