"""Background randomisation for lab-style photos.

Public sets like PlantVillage (maize) and the white-paper rice-leaf photos give
every class its own backdrop — black for rust, grey for leaf spot, white paper
for blast. A network happily learns the backdrop instead of the lesion, and
then fails on a farmer's field photo. Those backdrops are uniform, so the leaf
can be cut out (everything that differs from the border colour) and pasted onto
a real field background from the ICAR set. The label then only lives in the
leaf.

Used by data/ingest.py (to flag which images have a plain backdrop) and by
ml/train.py (to composite during training and for the background-swap test).
"""

from __future__ import annotations

import random

import numpy as np
from PIL import Image, ImageFilter

BORDER = 6          # px of border sampled at 128 px working size
TOLERANCE = 38.0    # colour distance from the backdrop still counted as backdrop
PLAIN_MIN = 0.55    # share of border pixels near the backdrop colour to call it "plain"


def _border(a: np.ndarray) -> np.ndarray:
    return np.concatenate([a[:BORDER].reshape(-1, 3), a[-BORDER:].reshape(-1, 3),
                           a[:, :BORDER].reshape(-1, 3), a[:, -BORDER:].reshape(-1, 3)]).astype(np.float32)


def backdrop(img: Image.Image) -> tuple[np.ndarray, float]:
    """Median border colour and the share of border pixels close to it."""
    small = np.asarray(img.convert("RGB").resize((128, 128)), dtype=np.float32)
    b = _border(small)
    med = np.median(b, axis=0)
    near = (np.linalg.norm(b - med, axis=1) < TOLERANCE).mean()
    return med, float(near)


def is_plain(img: Image.Image) -> bool:
    return backdrop(img)[1] >= PLAIN_MIN


def foreground_mask(img: Image.Image) -> Image.Image:
    """Soft mask (L mode, 255 = leaf) for a photo on a uniform backdrop."""
    rgb = img.convert("RGB")
    med, _ = backdrop(rgb)
    a = np.asarray(rgb, dtype=np.float32)
    fg = (np.linalg.norm(a - med, axis=2) >= TOLERANCE).astype(np.uint8) * 255
    m = Image.fromarray(fg, "L")
    k = max(3, (min(rgb.size) // 90) | 1)  # odd kernel scaled to the image
    m = m.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))  # drop specks, keep the leaf
    return m.filter(ImageFilter.GaussianBlur(max(1, k // 2)))


def composite(img: Image.Image, bg: Image.Image, rng: random.Random | None = None) -> Image.Image:
    """Paste the leaf from a plain-backdrop photo onto a random crop of a field photo."""
    rng = rng or random
    fgimg = img.convert("RGB")
    w, h = fgimg.size
    bg = bg.convert("RGB")
    s = max(w / bg.width, h / bg.height) * rng.uniform(1.0, 1.6)
    bg = bg.resize((max(w, int(bg.width * s)), max(h, int(bg.height * s))))
    x, y = rng.randint(0, bg.width - w), rng.randint(0, bg.height - h)
    canvas = bg.crop((x, y, x + w, y + h))
    canvas.paste(fgimg, (0, 0), foreground_mask(fgimg))
    return canvas
