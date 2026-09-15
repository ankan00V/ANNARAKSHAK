# AnnRakshak vision model — report (v2 CANDIDATE — rejected by the deploy gate; v3 warm start replaced it)

Generated 2026-09-15 07:06 UTC by `ml/train.py --with-extra`. Version `icar+extra-efficientnet_v2_s-warmstart-20260915`.

**Data:** ICAR rice & maize images (835 unique) + Crop Diseases compilation (rice blast, brown spot, healthy; PlantVillage maize rust, northern leaf blight, healthy) + CCMT field maize (fall armyworm, healthy); lab-backdrop photos trained with background randomisation. 20 training classes → 18 targets (rice leaf and neck blast, fall armyworm larvae and damage, are separate classes merged into one advisory target). The ICAR train/validation/test split is the one the previous model used, so the ICAR test numbers below compare like for like. Extra sources are split per class (70/15/15, seed 42) and capped (new classes ≤300 train images, classes ICAR already has ≤150); training samples classes evenly and, inside a class, gives the ICAR field photos 75% of the weight. **Warm start:** training continues from the deployed model — its backbone and its head rows for every class it already knew — at a third of the usual learning rate, so only the new classes are learnt from scratch (continual learning).

**Why background randomisation:** the extra rice photos are single leaves on white paper and the maize ones are PlantVillage leaves on black/grey — each class with its own backdrop. A network learns the backdrop. So 85% of the time in training (and always in validation) the leaf is cut out and pasted on a healthy ICAR field photo of the same crop (`ml/composite.py`). The background-swap test below pastes held-out test leaves on held-out field backgrounds: if the model had learnt backdrops, it would fail there.

## 1. ICAR field test set (same 126 images as the previous model)

| | Top-1 accuracy | Macro-F1 | Advised | Accuracy when advised | Calibration error |
|---|---|---|---|---|---|
| previous (icar-efficientnet_v2_s-finetune-20260914) | 0.897 | 0.895 | 86.5% | 0.9725 | 0.0552 |
| **this model** | 0.881 | 0.879 | 61.1% | 0.987 | 0.2339 |

## 2. Extra-source test images

- Original backgrounds: accuracy **0.289** (522 images); gate advises 6.9%, right 0.9722 of the time.
- Plain-backdrop images only: 0.177 on the original backdrop → **0.243** with the backdrop swapped for an unseen field photo (gate right 0.5625 of the time when it advises).

Per-class recall, background swapped:

| Class | Test images | Recall |
|---|---|---|
| maize_common_rust | 66 | 0.00 |
| maize_healthy | 19 | 0.37 |
| maize_turcicum_leaf_blight | 11 | 0.64 |
| rice_brown_spot | 60 | 0.52 |
| rice_healthy | 60 | 0.72 |
| rice_leaf_blast | 79 | 0.00 |
| rice_neck_blast | 67 | 0.00 |

## 3. Deployment checks

- ✅ ICAR test top-1 within 2 points of deployed: 0.881 vs 0.897
- ✅ ICAR accuracy-when-advised within 1 point of deployed: 0.987 vs 0.9725
- ❌ maize_common_rust recall after background swap >= 0.70: 0.000
- ❌ rice_leaf_blast recall after background swap >= 0.70: 0.000
- ❌ rice_neck_blast recall after background swap >= 0.70: 0.000

**Not deployed — the previous model stays live.**

![confusion matrix](candidate_confusion.png)

![Grad-CAM samples](candidate_gradcam.png)

## Read this before quoting the numbers

- The extra rice and maize photos are lab-style; field photos from farmers' phones will differ more than the swap test can show. Blast and rust are new photo classes: expert confirmations on the officials' dashboard are the field test that counts.
- The ICAR test is ~8 images per class; one image is ~12 points of per-class recall.
- The Crop Diseases download lost 1,695 relevant images to a damaged download (data/raw/crop_diseases/archive_LOST.txt); a clean re-download would add them.
