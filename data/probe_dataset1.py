import json
import os
import sys
import urllib.request

CATALOG_NID = "604953489"
BASE = "https://www.data.gov.in/backend/dataapi/v1"
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "application/json",
}

ENDPOINTS = {
    "catalog": f"{BASE}/api-export/catalog/{CATALOG_NID}?_format=json",
    "resources": f"{BASE}/api-export/resources/{CATALOG_NID}?_format=json",
}


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def summarize(payload):
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("data") or payload.get("resources") or payload.get("records") or [payload]
    else:
        items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        keep = {}
        for k, v in item.items():
            if any(s in k.lower() for s in ("title", "format", "file", "url", "size", "field", "name", "type")):
                keep[k] = v
        print(json.dumps(keep, indent=2)[:1200])
        print("-" * 60)


def main():
    os.makedirs("data/raw", exist_ok=True)
    ok = True
    for name, url in ENDPOINTS.items():
        print(f"== {name}: {url}")
        try:
            payload = get(url)
        except Exception as e:
            print(f"FAILED: {e}")
            ok = False
            continue
        path = f"data/raw/dataset1_{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"saved {path} ({os.path.getsize(path)} bytes)")
        summarize(payload)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
