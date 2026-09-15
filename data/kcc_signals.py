"""Turn the Kisan Call Centre pull (data/raw/kcc, see kcc_pull.py) into a small
committed signal file: when, and where, Maharashtra's farmers call about each
pest or disease group on our four crops.

    .venv/bin/python data/kcc_signals.py     -> backend/kb/kcc_signals.json

A call is matched to a signal group by keywords in the query text (mostly
English, written by the call-centre agent). Groups follow how farmers and
agents actually speak: "sucking pest" covers whitefly, jassid, aphid and
thrips together, so it is one group linked to those targets rather than a
guess at one of them. Counts are CALLS — how often farmers needed help — not
incidence; a district with more phones calls more. The file says so.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "kcc"
OUT = ROOT / "backend" / "kb" / "kcc_signals.json"

# (group id, crop, English label, our KB targets, keywords matched on the lower-cased query)
GROUPS = [
    ("cotton_pink_bollworm", "cotton", "Pink bollworm", ["cotton_pink_bollworm"], [r"pink ?boll", r"\bpbw\b", r"gulabi"]),
    ("cotton_american_bollworm", "cotton", "American bollworm", ["cotton_american_bollworm"],
     [r"american ?boll", r"helicoverpa", r"heliothis", r"green ?boll ?worm"]),
    ("cotton_sucking_pests", "cotton", "Sucking pests (whitefly, jassid, aphid, thrips)", ["cotton_whitefly", "cotton_jassid"],
     [r"sucking", r"white ?fly", r"jassid", r"hopper", r"aphid", r"thrip", r"mealy ?bug"]),
    ("cotton_boll_rot_leaf_red", "cotton", "Leaf reddening / boll rot", [], [r"red(dening)? ?lea", r"lalya", r"boll ?rot"]),
    ("soybean_girdle_beetle", "soybean", "Girdle beetle", ["soybean_girdle_beetle"], [r"girdle"]),
    ("soybean_caterpillars", "soybean", "Leaf-eating caterpillars (tobacco caterpillar, semilooper)",
     ["soybean_tobacco_caterpillar"], [r"caterpillar", r"spodoptera", r"semi ?looper", r"\blarva", r"leaf eat"]),
    ("soybean_yellow_mosaic", "soybean", "Yellow mosaic", ["soybean_yellow_mosaic"], [r"mosaic", r"\bymv\b"]),
    ("soybean_rust", "soybean", "Rust", ["soybean_rust"], [r"\brust"]),
    ("rice_blast", "rice", "Blast", ["rice_blast"], [r"blast", r"neck ?rot"]),
    ("rice_blight", "rice", "Blight (bacterial / sheath)", ["rice_bacterial_leaf_blight", "rice_sheath_blight"], [r"blight"]),
    ("rice_stem_borer", "rice", "Stem borer", ["rice_yellow_stem_borer", "rice_white_stem_borer"],
     [r"stem ?borer", r"dead ?heart", r"white ?ear", r"\bborer"]),
    ("rice_planthopper", "rice", "Planthoppers", ["rice_brown_planthopper"], [r"plant ?hopper", r"\bbph\b", r"hopper"]),
    ("rice_leaf_folder", "rice", "Leaf folder", ["rice_leaf_folder"], [r"leaf ?fold", r"leaf ?roll"]),
    ("rice_false_smut", "rice", "False smut", ["rice_false_smut"], [r"smut"]),
    ("maize_fall_armyworm", "maize", "Fall armyworm", ["maize_fall_armyworm"],
     [r"fall ?army", r"army ?worm", r"fall ?worm", r"\bfaw\b", r"spodoptera", r"leaf eat", r"caterpillar"]),
    ("maize_stem_borer", "maize", "Stem borer", ["maize_stem_borer"], [r"stem ?borer", r"\bborer"]),
    ("maize_leaf_blights", "maize", "Leaf blights", ["maize_turcicum_leaf_blight", "maize_maydis_leaf_blight"], [r"blight"]),
    ("maize_rust", "maize", "Rust", ["maize_common_rust"], [r"\brust"]),
    ("maize_aphid", "maize", "Aphid", ["maize_aphid"], [r"aphid"]),
]
COMPILED = [(g, c, lbl, tg, [re.compile(k) for k in kws]) for g, c, lbl, tg, kws in GROUPS]
KCC_DISTRICT_FIXES = {"NASIK": "Nashik", "AHMADNAGAR": "Ahmednagar", "BID": "Beed", "BULDANA": "Buldhana",
                      "GONDIYA": "Gondia", "RAIGARH": "Raigad", "OSMANABAD": "Dharashiv", "SANGALI": "Sangli",
                      "AURANGABAD": "Chhatrapati Sambhajinagar", "MUMBAI SUBURBAN": "Mumbai Suburban"}


def district(name: str) -> str:
    n = (name or "").strip().upper()
    return KCC_DISTRICT_FIXES.get(n, n.title())


def main() -> None:
    files = sorted(RAW.glob("*.jsonl"))
    if not files:
        raise SystemExit("no KCC data: run data/kcc_pull.py first")
    by_month: dict[str, Counter] = defaultdict(Counter)
    by_year: dict[str, Counter] = defaultdict(Counter)
    by_district: dict[str, Counter] = defaultdict(Counter)
    district_month: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    crop_total, crop_matched = Counter(), Counter()
    years = set()
    for f in files:
        crop = f.stem.split("_")[0]
        for line in f.open(encoding="utf-8"):
            r = json.loads(line)
            q = f"{r.get('QueryText') or ''}".lower()
            try:
                y, m = int(r["year"]), int(r["month"])
            except (KeyError, TypeError, ValueError):
                continue
            years.add(y)
            crop_total[crop] += 1
            hit = False
            for gid, gcrop, _, _, pats in COMPILED:
                if gcrop == crop and any(p.search(q) for p in pats):
                    hit = True
                    by_month[gid][m] += 1
                    by_year[gid][y] += 1
                    d = district(r.get("DistrictName"))
                    by_district[gid][d] += 1
                    district_month[gid][d][m] += 1
            crop_matched[crop] += hit

    groups = []
    for gid, crop, label, targets, _ in COMPILED:
        total = sum(by_month[gid].values())
        if not total:
            continue
        share = {m: round(by_month[gid][m] / total, 4) for m in range(1, 13)}
        mean = 1 / 12
        peak = [m for m in range(1, 13) if share[m] >= 1.5 * mean]
        groups.append({
            "id": gid, "crop": crop, "label": label, "targets": targets, "calls": total,
            "month_share": share, "peak_months": peak,
            "by_year": {str(y): by_year[gid][y] for y in sorted(by_year[gid])},
            "top_districts": [{"district": d, "calls": n} for d, n in by_district[gid].most_common(10)],
            "district_months": {d: {str(m): n for m, n in sorted(ms.items())}
                                for d, ms in district_month[gid].items() if sum(ms.values()) >= 20},
        })
    out = {
        "_note": ("Kisan Call Centre plant-protection calls from Maharashtra farmers, grouped by pest/disease "
                  "with keyword rules (data/kcc_signals.py). Counts are calls — how often farmers asked for help — "
                  "not incidence; call volume also reflects phone access and awareness."),
        "source": "data.gov.in — Kisan Call Centre (KCC) transcripts of farmers' queries & answers (Ministry of Agriculture & Farmers Welfare)",
        "state": "MAHARASHTRA", "query_type": "Plant Protection",
        "years": [min(years), max(years)], "built": date.today().isoformat(),
        "coverage": {c: {"calls": crop_total[c], "matched": crop_matched[c],
                         "matched_pct": round(100 * crop_matched[c] / crop_total[c], 1)} for c in sorted(crop_total)},
        "groups": sorted(groups, key=lambda g: -g["calls"]),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(groups)} groups")
    for c, v in out["coverage"].items():
        print(f"  {c}: {v['matched']}/{v['calls']} calls matched ({v['matched_pct']}%)")
    for g in out["groups"]:
        print(f"  {g['id']:28s} {g['calls']:6d} calls  peak {g['peak_months']}  top {g['top_districts'][0]['district']}")


if __name__ == "__main__":
    main()
