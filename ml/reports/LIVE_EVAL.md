# End-to-end accuracy — photo and live video call

Generated 2026-09-15 15:41 by `ml/live_eval.py` with model `icar+extra-efficientnet_v2_s-warmstart-20260915`, through the real API (confidence gate, Doubt Doctor, live walk). Held-out images only: the ICAR test split (same as the model report) and up to 20 held-out images per class from the extra sources.

## 1. Photo diagnosis

| Images | Advised | Right when advised | Asked a question | Sent to expert | Asked for a retake |
|---|---|---|---|---|---|
| 469 | 412 (88%) | **94.2%** | 0 | 29 | 28 |

- ICAR field photos: 126 images, advised 115, right when advised 95.7%
- Extra sources (blast, rust, field FAW…): 343 images, advised 297, right when advised 93.6%

Advised but wrong (what a farmer would have been told):

- maize_fall_armyworm_damage → maize_healthy
- maize_maydis_leaf_blight → maize_curvularia_leaf_spot
- maize_turcicum_leaf_blight → maize_common_rust
- maize_turcicum_leaf_blight → maize_common_rust
- maize_turcicum_leaf_blight → maize_common_rust
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_brown_spot → rice_blast
- rice_healthy → rice_blast
- rice_healthy → rice_blast
- rice_healthy → rice_brown_spot
- rice_healthy → rice_brown_spot
- rice_leaf_blast → rice_brown_spot
- rice_skipper → rice_yellow_stem_borer
- rice_yellow_stem_borer → rice_blast

## 2. Live video call — one full session per class

A session walks the real steps: held-out healthy field photos for the field, plant and base steps, and that class's held-out leaves for the close-ups (lab photos pasted on held-out field backgrounds), each frame a slightly moved, turned and relit view, as a phone gives. **Right** = the true problem is reported as seen (≥ 2 separate close-ups agreeing) — or, for a healthy class, nothing is reported as seen. **Cautious** = shown as *possible* and sent to an expert. **Wrong** = a different problem reported as seen.

| Class | Frames | Verdict | Seen | Possible | Result |
|---|---|---|---|---|---|
| maize_aphid | 17 | found | maize_aphid | — | right |
| maize_common_rust | 17 | found | maize_common_rust | — | right |
| maize_curvularia_leaf_spot | 17 | found | maize_curvularia_leaf_spot | — | right |
| maize_downy_mildew | 19 | found | maize_downy_mildew | — | right |
| maize_fall_armyworm | 20 | found | maize_fall_armyworm | — | right |
| maize_fall_armyworm_damage | 18 | found | maize_fall_armyworm | — | right |
| maize_healthy | 21 | check | — | maize_fall_armyworm | right |
| maize_maydis_leaf_blight | 18 | found | maize_maydis_leaf_blight, maize_turcicum_leaf_blight | — | right (+ another) |
| maize_turcicum_leaf_blight | 23 | found | maize_turcicum_leaf_blight | maize_fall_armyworm, maize_common_rust | right |
| rice_bacterial_leaf_blight | 20 | found | rice_bacterial_leaf_blight | rice_brown_spot | right |
| rice_brown_spot | 17 | found | rice_brown_spot, rice_blast | — | right (+ another) |
| rice_false_smut | 23 | found | rice_false_smut | — | right |
| rice_healthy | 17 | found | rice_blast | — | wrong |
| rice_leaf_blast | 17 | found | rice_blast | — | right |
| rice_leaf_folder | 20 | found | rice_leaf_folder | rice_skipper, rice_yellow_stem_borer, rice_blast | right |
| rice_neck_blast | 19 | found | rice_blast | — | right |
| rice_sheath_blight | 19 | found | rice_sheath_blight | — | right |
| rice_skipper | 24 | found | rice_skipper | rice_yellow_stem_borer | right |
| rice_white_stem_borer | 17 | found | rice_white_stem_borer | — | right |
| rice_yellow_stem_borer | 17 | found | rice_yellow_stem_borer, rice_blast | — | right (+ another) |

**Right 19/20** · cautious 0 · missed 0 · wrong 1.

## Read this before quoting the numbers

- Held-out images are still curated datasets; a phone in a real field adds blur, glare and mixed plants — which the live walk's quality checks and the two-close-up rule exist to absorb.
- A live session here streams still images of one class; a real field can hold two problems at once.
- Expert confirmations on the officials' dashboard are the field accuracy that counts.
