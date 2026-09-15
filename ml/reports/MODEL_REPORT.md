# AnnRakshak vision model — report

Generated 2026-09-14 13:22 UTC by `ml/train.py`.

**Data:** ICAR Crop Disease and Insect-pest Image Dataset for Rice and Maize (835 unique images); 17 training classes (fall armyworm larvae and damage are separate classes merged into one advisory target). Stratified split, seed 42: 584 train / 125 validation / 126 test. Exact duplicate images were removed before splitting so no photo appears on both sides.

## Model comparison (held-out test set)

| Model | Val macro-F1 | Test accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|
| densenet201 + ANN (frozen) | 0.798 | 0.818 | 0.834 | 0.820 | 0.818 |
| efficientnet_v2_s + ANN (frozen) | 0.787 | 0.825 | 0.840 | 0.828 | 0.823 |
| mobilenet_v3_large + ANN (frozen) | 0.803 | 0.794 | 0.828 | 0.795 | 0.791 |
| efficientnet_v2_s fine-tuned | 0.863 | 0.897 | 0.908 | 0.899 | 0.895 |

Deployed: **efficientnet_v2_s fine-tuned** (best validation macro-F1). Version `icar-efficientnet_v2_s-finetune-20260914`.

## Calibration

Softmax temperature fitted on validation: **T = 0.802**. Expected calibration error on test: 0.134 → **0.055**. Calibrated confidence is what the gate compares against its thresholds.

## The confidence gate on the test set

Every test image run through the production gate (same code as the API), using the image's own crop as the farm crop:

- Advised directly: **86.5%** of images, and **97.2%** of those advisories were correct (vs 89.7% raw top-1 accuracy).
- Sent to the Doubt Doctor: 0.8% — the true label was one of the two candidates in 100.0% of those.
- Escalated to an expert: 12.7%.

## Per-class results (deployed model, test set)

| Class | Precision | Recall | F1 | Test images |
|---|---|---|---|---|
| maize_aphid | 0.88 | 1.00 | 0.93 | 7 |
| maize_curvularia_leaf_spot | 0.88 | 1.00 | 0.93 | 7 |
| maize_downy_mildew | 0.89 | 1.00 | 0.94 | 8 |
| maize_fall_armyworm | 1.00 | 1.00 | 1.00 | 7 |
| maize_fall_armyworm_damage | 1.00 | 0.88 | 0.93 | 8 |
| maize_healthy | 0.88 | 1.00 | 0.93 | 7 |
| maize_maydis_leaf_blight | 0.86 | 0.75 | 0.80 | 8 |
| maize_turcicum_leaf_blight | 0.88 | 0.88 | 0.88 | 8 |
| rice_bacterial_leaf_blight | 0.67 | 0.86 | 0.75 | 7 |
| rice_brown_spot | 0.88 | 0.88 | 0.88 | 8 |
| rice_false_smut | 1.00 | 0.88 | 0.93 | 8 |
| rice_healthy | 0.78 | 1.00 | 0.88 | 7 |
| rice_leaf_folder | 1.00 | 0.75 | 0.86 | 8 |
| rice_sheath_blight | 1.00 | 0.86 | 0.92 | 7 |
| rice_skipper | 0.88 | 1.00 | 0.93 | 7 |
| rice_white_stem_borer | 1.00 | 1.00 | 1.00 | 7 |
| rice_yellow_stem_borer | 1.00 | 0.57 | 0.73 | 7 |

![confusion matrix](confusion_matrix.png)

![Grad-CAM samples](gradcam_samples.png)

## Read this before quoting the numbers

- ~50 images per class and a test set of about 8 images per class: one image is ~12 points of per-class recall. Treat per-class numbers as indicative.
- The images come from one dataset; field photos from farmers' phones will differ (lighting, framing, damage rather than the insect). Field accuracy is measured separately, from expert confirmations, on the officials' dashboard.
- The model cannot recognise diseases it was never shown (e.g. rice blast). Those stay on the risk-alert and inspection path; see data/DATASETS.md.
