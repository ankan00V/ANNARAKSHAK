"""Familiarity bank: reject photos that are not the kind of photo the model knows.

A softmax always names a class — even for a face in front of an ivy wall — and
the green-pixel check passes anything with plants behind it. This builds the
model's own feature vectors for every training photo; at run time a photo whose
features are far from all of them (mean cosine similarity to its k nearest
training photos below a threshold) is "not a crop photo" and the farmer is
asked to retake it, in the photo path and in the live walk.

The threshold is set on held-out crop photos so that about 1% of genuine ones
are rejected (a retake, never a wrong answer), and checked against photos
that are not crop close-ups.

    .venv/bin/python ml/build_familiarity.py [--ood DIR ...]
      -> ml/artifacts/familiarity_bank.npy, ml/artifacts/familiarity.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
os.environ.pop("ANNRAKSHAK_VISION", None)
sys.path.insert(0, str(ROOT / "backend"))

from PIL import Image  # noqa: E402

from app.engine.model import Classifier  # noqa: E402

ART = ROOT / "ml" / "artifacts"
K = 5
REJECT_GENUINE = 0.01  # the share of held-out crop photos we accept asking to retake


def embed_all(clf: Classifier, paths: list[Path], batch: int = 32) -> np.ndarray:
    out = []
    for i in range(0, len(paths), batch):
        xs = []
        for p in paths[i:i + batch]:
            with Image.open(p) as im:
                xs.append(clf.tf(im.convert("RGB")))
        with torch.no_grad():
            f = torch.nn.functional.normalize(clf.model.pooled(torch.stack(xs)), dim=1)
        out.append(f.numpy())
        print(f"  {min(i + batch, len(paths))}/{len(paths)}", flush=True)
    return np.concatenate(out)


def scores(bank: np.ndarray, feats: np.ndarray, skip_self: bool = False) -> np.ndarray:
    sims = feats @ bank.T
    if skip_self:
        sims = np.where(sims > 0.9999, -1, sims)
    top = np.sort(sims, axis=1)[:, -K:]
    return top.mean(axis=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ood", nargs="*", default=[], help="folders of photos that are not crop close-ups")
    args = ap.parse_args()
    meta = json.loads((ART / "meta.json").read_text())
    clf = Classifier(ART, meta)
    split = json.loads((ART / "split.json").read_text())
    train = [ROOT / p for p in split["train"] + split.get("extra_train", [])]
    held = [ROOT / p for p in split["test"] + split.get("extra_test", []) + split["val"] + split.get("extra_val", [])]
    print(f"bank from {len(train)} training photos; threshold from {len(held)} held-out photos")
    bank = embed_all(clf, train)
    genuine = scores(bank, embed_all(clf, held))
    threshold = float(np.quantile(genuine, REJECT_GENUINE))
    report = {"model_version": clf.version, "k": K, "threshold": round(threshold, 4),
              "bank_size": len(bank), "held_out": len(held),
              "held_out_quantiles": {q: round(float(np.quantile(genuine, q)), 4) for q in (0.01, 0.05, 0.5)},
              "rejects_genuine_pct": round(100 * float((genuine < threshold).mean()), 2)}
    ood = [p for d in args.ood for p in sorted(Path(d).glob("*")) if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    if ood:
        o = scores(bank, embed_all(clf, ood))
        report["ood"] = {"photos": len(ood), "rejected_pct": round(100 * float((o < threshold).mean()), 1),
                         "max": round(float(o.max()), 4), "median": round(float(np.median(o)), 4),
                         "passed": [p.name for p, s in zip(ood, o) if s >= threshold]}
    np.save(ART / "familiarity_bank.npy", bank.astype(np.float16))
    (ART / "familiarity.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
