"""Pull Kisan Call Centre plant-protection queries for Maharashtra from the
data.gov.in OGD API into data/raw/kcc/ (gitignored).

    .venv/bin/python data/kcc_pull.py            # resumable; re-run to continue
    .venv/bin/python data/kcc_pull.py --probe    # counts only

Scope: StateName=MAHARASHTRA, QueryType=Plant Protection, our four crops,
every year the API has. One JSONL file per (crop, year); a .done marker per
file makes the pull resumable after a timeout or a closed laptop.

Network note: api.data.gov.in hangs on this machine's default route but answers
over IPv4 with a browser User-Agent, so the client forces both.
Key: DATA_GOV_IN_API_KEY in .env (never logged).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "kcc"
URL = "https://api.data.gov.in/resource/cef25fe2-9231-4128-8aec-2c948fedd43f"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
PAGE = 1000
CROPS = {  # our crop id -> KCC's Crop value
    "rice": "Paddy (Dhan)",
    "maize": "Maize (Makka)",
    "cotton": "Cotton (Kapas)",
    "soybean": "Soybean (bhat)",
}
YEARS = range(2008, 2027)


def client() -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(60.0, connect=15.0),
        headers={"User-Agent": UA, "Accept": "application/json"},
        transport=httpx.HTTPTransport(local_address="0.0.0.0", retries=2),  # IPv4 only
    )


def get(c: httpx.Client, key: str, crop: str, year: int, offset: int, limit: int) -> dict:
    params = {
        "api-key": key, "format": "json", "offset": offset, "limit": limit,
        "filters[StateName]": "MAHARASHTRA", "filters[QueryType]": "Plant Protection",
        "filters[Crop]": crop, "filters[year]": str(year),
    }
    for attempt in range(5):
        try:
            r = c.get(URL, params=params)
            if r.status_code == 200:
                return r.json()
            print(f"    HTTP {r.status_code}, retrying", flush=True)
        except (httpx.HTTPError, ValueError) as e:
            print(f"    {type(e).__name__}, retrying", flush=True)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"gave up on {crop} {year} @ {offset}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="print record counts and stop")
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")
    key = os.environ.get("DATA_GOV_IN_API_KEY")
    if not key:
        sys.exit("DATA_GOV_IN_API_KEY missing from .env")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with client() as c:
        for cid, crop in CROPS.items():
            for year in YEARS:
                f = OUT / f"{cid}_{year}.jsonl"
                done = f.with_suffix(".done")
                if done.exists():
                    manifest[f.name] = json.loads(done.read_text())
                    continue
                total = int(get(c, key, crop, year, 0, 1).get("total") or 0)
                print(f"{cid} {year}: {total} records", flush=True)
                if args.probe or total == 0:
                    if not args.probe:
                        done.write_text(json.dumps({"records": 0}))
                    continue
                have = sum(1 for _ in f.open()) if f.exists() else 0
                with f.open("a", encoding="utf-8") as out:
                    offset = have
                    while offset < total:
                        recs = get(c, key, crop, year, offset, PAGE).get("records") or []
                        if not recs:
                            break
                        for r in recs:
                            out.write(json.dumps(r, ensure_ascii=False) + "\n")
                        offset += len(recs)
                        print(f"  {cid} {year}: {offset}/{total}", flush=True)
                n = sum(1 for _ in f.open())
                meta = {"records": n, "api_total": total, "crop": crop, "year": year,
                        "pulled_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
                done.write_text(json.dumps(meta))
                manifest[f.name] = meta
    if not args.probe:
        (OUT / "MANIFEST.json").write_text(json.dumps({
            "source": "data.gov.in OGD API — Kisan Call Centre (KCC) transcripts of farmers' queries & answers",
            "resource": URL, "filters": {"StateName": "MAHARASHTRA", "QueryType": "Plant Protection",
                                         "Crop": list(CROPS.values())},
            "files": manifest}, indent=2))
        print("done:", sum(m.get("records", 0) for m in manifest.values()), "records")


if __name__ == "__main__":
    main()
