# Manual dataset downloads

This machine cannot reach Indian gov data hosts — `www.data.gov.in/backend/dataapi/v1`
(the API every catalog page loads its file list from) and `aps.dac.gov.in` both hang
from here (HTTP 000, IPv4 forced too), while the public pages themselves load fine.
Wayback has no captures. So: download these in a browser and drop them into the
paths below (`data/raw/` is gitignored — they will never be committed).

Already confirmed from the catalog metadata embedded in the pages:

| # | Dataset | nid | What we know |
|---|---------|-----|--------------|
| 1 | Crop Disease and Pest Image Data | 604953489 | annotated IMAGES (ICAR-IASRI); expect a zip or external link on the page |
| 2 | District-wise, season-wise crop production statistics from 1997 | 87630 | **direct file: https://aps.dac.gov.in/APY/apy.csv** (text/csv, 15.3 MB) |
| 3 | Rainfall in India (IMD) | 1090541 | resource list behind blocked API |
| 4 | All India Seasonal and Annual Temperature Series (IMD) | 6803256 | resource list behind blocked API |
| 5 | Kisan Call Centre farmer queries | 2373501 | resource list behind blocked API |
| 6 | ICAR Technologies | 6672116 | resource list behind blocked API |

Where to drop files (create dirs if missing):

```
data/raw/dataset1_crop_disease_pest/     <- images (unzipped) from #1
data/raw/crop_production_apy.csv         <- direct apy.csv from #2
data/raw/rainfall_india/                 <- whatever CSVs #3 gives
data/raw/temperature_series/             <- whatever CSVs #4 gives
data/raw/kcc_queries/                    <- whatever CSVs #5 gives
data/raw/icar_technologies/              <- whatever CSVs #6 gives
```

How to find each file on the page (takes ~2 min per dataset):

1. Open the catalog URL in a normal browser.
2. Scroll to the "Resources" section — each row has CSV / XLSX / API buttons.
3. Click the CSV (or the download icon); for #1 take the zip/external link instead.
4. For #2 you can skip the page and use https://aps.dac.gov.in/APY/apy.csv directly.

Fallback if a catalog shows no downloadable rows: grab a free API key at
data.gov.in (My Account → API key) and I'll wire ingestion through the v3 API
from a network that can reach `api.data.gov.in`.

Once files land in `data/raw/`, tell me which ones arrived — I'll verify schemas
before any ingestion or training code is written.
