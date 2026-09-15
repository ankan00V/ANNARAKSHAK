# Dataset 1 — Crop Disease and Pest Image Data (ICAR)

Catalog: https://www.data.gov.in/catalog/crop-disease-and-pest-image-data
Status as of Sep 12, 2026: catalog metadata VERIFIED from the live page's SSR
payload. Resource-level file listing NOT YET obtained — see blocker below.

## Verified catalog metadata (from `window.__NUXT__` payload, live page)

- Title: Crop Disease and Pest Image Data
- Description: "This catalog contains the annotated images of Crop Diseases and Pests"
- Publisher: Dr Rajender Parsad, Principal Scientist, ICAR — Indian Agriculture
  Statistics Research Institute (IASRI), Library Avenue, Pusa, New Delhi-110012
  (email obfuscated on page: rajender [dot] parsad [at] icar [dot] gov [dot] in,
  phone +91 1125843573)
- Ministry chain: Ministry of Agriculture and Farmers Welfare → DARE → ICAR
- Sector: Agriculture || Plant Protection
- Keywords: Plant Protection, Pests, Computer Vision, Crop Diseases
- Jurisdiction: All India
- Catalog nid: 604953489, uuid 6ce86d4c-03f6-4d7d-8cff-9f16e3410c66
- Moderation state: Published, updated 25/08/2026

Key fact for ingestion: this is an IMAGE dataset ("annotated images"), so expect
the resource to be an archive (zip) download and/or a linked external host —
not a CSV-style data.gov.in table API. The real format/size/classes get
confirmed from the resource record itself (see blocker).

## Resolved Sep 14, 2026 — resource identified

The catalog has exactly one resource (via `backend/dmspublic/v1/resources`,
read from the in-app browser):

- Title: ICAR Crop Disease and Insect-pest Image Dataset for Rice and Maize
- nid 604953507, uuid 1d946612-d771-49dc-a11c-a68c7bca091f
- `application/zip`, 970,886,204 bytes (~926 MB), one-time
- Access: Registered ("Only registered users can download the dataset."),
  licence: ICAR Data Use License
- Scope: **rice and maize only** — class list comes from the zip itself

Download is manual (login), see `MANUAL_DOWNLOADS.md`. The blocker below is
kept for history.

## Blocker (Sep 12, superseded)

The page is a Nuxt SPA whose resource list loads client-side from:

    https://www.data.gov.in/backend/dataapi/v1/api-export/catalog/604953489?_format=json
    https://www.data.gov.in/backend/dataapi/v1/api-export/resources/604953489?_format=json

That backend host hangs (connect timeout, HTTP 000, IPv4 forced too) from this
network while www.data.gov.in itself responds fine — consistent with the API
origin being geo-restricted or firewalled. Older public `api.data.gov.in`
catalog endpoint requires a registered key ("Key not authorised" with a demo
key). Wayback/CDX have no captures of this catalog.

## Next step (5 minutes on a network that reaches the API)

Run `python3 data/probe_dataset1.py`. It fetches both endpoints, saves raw JSON
under `data/raw/`, and prints resource titles, file formats, download URLs and
field names — everything needed to write the ingestion script before any model
code. If still blocked, register a free key at data.gov.in and use the v3
catalog endpoint `https://api.data.gov.in/catalog/<uuid>/resource/<rid>` as a
fallback, or pull the resource from ICAR-IASRI's own data portal if the
resource record points there.
