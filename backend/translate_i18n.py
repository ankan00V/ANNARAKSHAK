"""Build the machine-translated languages (Bengali, Tamil, Telugu, Kannada,
Malayalam, Gujarati, Punjabi, Odia) from the approved English.

    ../.venv/bin/python translate_i18n.py --count            # what would be sent, nothing sent
    ../.venv/bin/python translate_i18n.py --lang ta,bn       # translate what is missing
    ../.venv/bin/python translate_i18n.py                    # all eight

Two outputs per language, both committed and reviewable:
  backend/kb/i18n/<lang>.json              English source -> translation (KB + backend messages)
  frontend/landing/src/locales/<lang>.json UI key -> translation

Only missing strings are sent, so a re-run after a KB edit costs only the new
text. Placeholders ({crop}, {mm} ...) are protected and checked; a string whose
placeholders don't survive is left out (it shows in English). Pesticide verdicts
(app.engine.labelcheck) are never machine translated.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

from app.config import KB_DIR, SARVAM_TRANSLATE_MODEL
from app.i18n import MACHINE, MEMORY_DIR, translate_many

ROOT = Path(__file__).resolve().parents[1]
UI_SOURCE = ROOT / "frontend" / "landing" / "src" / "lib" / "i18n.ts"
UI_OUT = ROOT / "frontend" / "landing" / "src" / "locales"
KB_FILES = ["crops.json", "targets.json", "advisories.json", "cues.json", "risk_rules.json",
            "agromet.json", "icar_technologies.json"]
MODULES = ["app.services", "app.notify", "app.mailer", "app.live", "app.engine.advisory", "app.engine.risk",
           "app.engine.fieldnow", "app.engine.livescan", "app.routers.weather"]
NOTE = ("Machine translated with Sarvam-Translate from the approved English; placeholders checked. "
        "Pending review by a native speaker — correct any line in place, the job never overwrites an existing entry.")


def _walk(o, out: set[str]) -> None:
    if isinstance(o, dict):
        if "en" in o and ("hi" in o or "mr" in o):
            en = o["en"]
            if isinstance(en, str):
                out.add(en.strip())
            elif isinstance(en, list):
                out.update(x.strip() for x in en if isinstance(x, str))
        for k, v in o.items():
            if not str(k).startswith("_"):
                _walk(v, out)
    elif isinstance(o, (list, tuple)):
        for v in o:
            _walk(v, out)


def backend_strings() -> list[str]:
    out: set[str] = set()
    for f in KB_FILES:
        _walk(json.loads((KB_DIR / f).read_text(encoding="utf-8")), out)
    for m in MODULES:
        mod = importlib.import_module(m)
        for name, val in vars(mod).items():
            if name.isupper():
                _walk(val, out)
    return sorted(s for s in out if s)


UI_LINE = re.compile(r"""^\s{2}(['"]?)([\w+.\-]+)\1:\s*(['"])((?:\\.|(?!\3).)*)\3,?\s*$""")


def ui_strings() -> dict[str, str]:
    src = UI_SOURCE.read_text(encoding="utf-8")
    start = src.index("const en = {")
    body = src[start:src.index("\n}\n", start)]
    out = {}
    for line in body.splitlines()[1:]:
        m = UI_LINE.match(line)
        if m:
            out[m.group(2)] = bytes(m.group(4), "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8") \
                if "\\" in m.group(4) else m.group(4)
    return out


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=",".join(MACHINE))
    ap.add_argument("--count", action="store_true", help="only count what would be sent")
    args = ap.parse_args()
    langs = [x for x in args.lang.split(",") if x]
    bad = [x for x in langs if x not in MACHINE]
    if bad:
        sys.exit(f"not a machine-translated language: {bad} (choose from {MACHINE})")

    kb_src = backend_strings()
    ui_src = ui_strings()
    print(f"sources: {len(kb_src)} backend strings, {len(ui_src)} UI strings")
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    UI_OUT.mkdir(parents=True, exist_ok=True)
    for lang in langs:
        kb_path, ui_path = MEMORY_DIR / f"{lang}.json", UI_OUT / f"{lang}.json"
        kb_have = load(kb_path).get("strings", {})
        ui_have = load(ui_path)
        kb_todo = [s for s in kb_src if s not in kb_have]
        ui_todo = {k: v for k, v in ui_src.items() if k not in ui_have}
        chars = sum(map(len, kb_todo)) + sum(map(len, ui_todo.values()))
        print(f"{lang}: {len(kb_todo)} backend + {len(ui_todo)} UI strings to translate ({chars} chars)")
        if args.count or (not kb_todo and not ui_todo):
            continue
        t0 = time.time()
        texts = sorted(set(kb_todo) | set(ui_todo.values()))
        done = translate_many(texts, lang, progress=lambda i, n: print(f"  {lang}: {i}/{n}", flush=True))
        kb_have.update({s: done[s] for s in kb_todo if s in done})
        ui_have.update({k: done[v] for k, v in ui_todo.items() if v in done})
        kb_path.write_text(json.dumps({"_note": NOTE, "model": SARVAM_TRANSLATE_MODEL, "source": "en",
                                       "updated": date.today().isoformat(), "strings": dict(sorted(kb_have.items()))},
                                      ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        ui_path.write_text(json.dumps(dict(sorted(ui_have.items())), ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")
        missing = len(texts) - len(done)
        print(f"  {lang}: {len(done)}/{len(texts)} translated in {time.time() - t0:.0f}s"
              f"{f'; {missing} left in English (failed or lost a placeholder)' if missing else ''}")


if __name__ == "__main__":
    main()
