# Manual dataset downloads

Re-probed Sep 14, 2026. The catalog metadata is readable now (the in-app browser
reaches `www.data.gov.in/backend/*`; plain curl is still held open by the WAF), so
every resource below is identified exactly. But nothing can be fetched headlessly:

- data.gov.in serves files only through its Download dialog, which needs usage type,
  purpose, name/email/mobile and an image CAPTCHA. Direct `/files/ogdpv2dms/...`
  URLs return 403, even from a browser session.
- The image dataset (#1) is "Registered" access — login required.
- The two off-site mirrors don't answer from this machine: `aps.dac.gov.in` refuses
  the connection, `krishi.icar.gov.in` doesn't resolve.

So download these in a normal browser and drop them at the paths shown
(`data/raw/` is gitignored).

## Checklist

Received so far: #1 and #3a-3c plus the rest of the rainfall catalog (Sep 14); #6 as rows pasted into chat (Sep 15) — see `DATASETS.md`. Still needed: #2, #3d, #4, #5, and the #6 CSV file itself so ingest can cross-check it.

| # | Resource (exact title on the page) | Size | Access | Save to |
|---|---|---|---|---|
| 1 | ✅ received — ICAR Crop Disease and Insect-pest Image Dataset for Rice and Maize | 926 MB zip | **login required** | `data/raw/icar_rice_maize/` (unzipped) |
| 2 | District-wise, season-wise crop production statistics from 1997 | 15.3 MB csv | public | `data/raw/crop_production_apy.csv` |
| 3a | ✅ received — Sub Divisional Monthly Rainfall from 1901 to 2017 | 445 KB csv | public | `data/raw/rainfall/` |
| 3b | ✅ received — Area weighted monthly, seasonal and annual rainfall (in mm) for 36 meteorological subdivisions from 1901-2015 | 528 KB csv | public | `data/raw/rainfall/` |
| 3c | ✅ received — All India area weighted monthly, seasonal and annual rainfall (in mm) from 1901-2015 | 14 KB csv | public | `data/raw/rainfall/` |
| 3d | District Rainfall Normal (in mm) Monthly, Seasonal And Annual : Data Period 1951-2000 | 168 KB csv | public | `data/raw/rainfall/` |
| 4 | Temperature series 1901-2021 — the 5 files titled "…for the period 1901-2021" (mean, min, max, min/max, seasonal mean) | ~50 KB total | public | `data/raw/temperature_series/` |
| 5 | Kisan Call Centre (KCC) - Transcripts of farmers queries & answers | large, API/JSON-backed | public | `data/raw/kcc_queries/` |
| 6 | ◐ rows received (pasted), file still wanted — ICAR Technology Repository | 2.7 MB csv | public | `data/raw/icar_technologies/` |

Pages:

1. https://www.data.gov.in/catalog/crop-disease-and-pest-image-data
2. https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997
   (or https://aps.dac.gov.in/APY/apy.csv directly — same file, no form)
3. https://www.data.gov.in/catalog/rainfall-india (3a-3c) and
   https://www.data.gov.in/resource/district-rainfall-normal-mm-monthly-seasonal-and-annual-data-period-1951-2000 (3d)
4. https://www.data.gov.in/catalog/all-india-seasonal-and-annual-temperature-series
5. https://www.data.gov.in/resource/kisan-call-centre-kcc-transcripts-farmers-queries-answers
   — if the full export is too big, a Maharashtra-only filter is enough.
6. https://www.data.gov.in/resource/icar-technology-repository

Skip the other 10 resources in the rainfall catalog — they're monsoon-only
departure summaries already covered by 3a/3b.

Download dialog: pick Non-commercial, purpose Academia/R&D, fill the CAPTCHA.

Once files land, say which arrived and I'll verify schemas before writing any
ingestion or training code.
