"""Model architecture, preprocessing, inference and Grad-CAM — shared by
ml/train.py and the API so training and serving cannot drift apart.

Two families, following the two reference papers:
  * "finetune": an ImageNet backbone fine-tuned end to end (Haider et al.,
    VTSE 2024, EfficientNetV2 transfer learning).
  * "ann":      a frozen ImageNet backbone feeding a 1024-512-256-128 ANN
    head (Singh et al., IJCISIM 2026, DenseNet201 features + ANN).
Both are one nn.Module (features -> pool -> head), so Grad-CAM works the same
way on either.

Only imported when trained artifacts exist; the API keeps running on the stub
when torch or the artifacts are absent.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)

BACKBONES = {
    # name: (constructor, weights enum, feature dim)
    "efficientnet_v2_s": (models.efficientnet_v2_s, models.EfficientNet_V2_S_Weights.IMAGENET1K_V1, 1280),
    "densenet201": (models.densenet201, models.DenseNet201_Weights.IMAGENET1K_V1, 1920),
    "mobilenet_v3_large": (models.mobilenet_v3_large, models.MobileNet_V3_Large_Weights.IMAGENET1K_V2, 960),
}


class Net(nn.Module):
    def __init__(self, backbone: str, n_classes: int, head: str, pretrained: bool = True):
        super().__init__()
        ctor, weights, dim = BACKBONES[backbone]
        base = ctor(weights=weights if pretrained else None)
        self.features = base.features
        self.needs_relu = backbone == "densenet201"  # torchvision applies it in forward()
        if head == "ann":
            self.head = nn.Sequential(
                nn.Linear(dim, 1024), nn.ReLU(), nn.Dropout(0.4),
                nn.Linear(1024, 512), nn.ReLU(), nn.Dropout(0.3),
                nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.2),
                nn.Linear(256, 128), nn.ReLU(),
                nn.Linear(128, n_classes),
            )
        else:
            self.head = nn.Sequential(nn.Dropout(0.3), nn.Linear(dim, n_classes))

    def feature_map(self, x: torch.Tensor) -> torch.Tensor:
        f = self.features(x)
        return F.relu(f) if self.needs_relu else f

    def pooled(self, x: torch.Tensor) -> torch.Tensor:
        return torch.flatten(F.adaptive_avg_pool2d(self.feature_map(x), 1), 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.pooled(x))


def test_transform(size: int):
    return transforms.Compose([
        transforms.Resize(int(size * 1.14)),
        transforms.CenterCrop(size),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


def train_transform(size: int):
    return transforms.Compose([
        transforms.RandomResizedCrop(size, scale=(0.45, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomApply([transforms.RandomRotation(90)], p=0.5),
        transforms.ColorJitter(0.3, 0.3, 0.3, 0.03),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


def best_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def gradcam(model: Net, x: torch.Tensor, class_idx: int) -> np.ndarray:
    """Grad-CAM on the last feature map: which regions pushed the score for
    `class_idx` up. Returns an HxW array in [0, 1]."""
    model.zero_grad(set_to_none=True)
    fmap = model.feature_map(x)
    fmap.retain_grad()
    logits = model.head(torch.flatten(F.adaptive_avg_pool2d(fmap, 1), 1))
    logits[0, class_idx].backward()
    weights = fmap.grad.mean(dim=(2, 3), keepdim=True)
    cam = F.relu((weights * fmap).sum(dim=1))[0]
    cam = cam - cam.min()
    cam = cam / (cam.max() + 1e-8)
    return cam.detach().cpu().numpy()


class Classifier:
    """Loads ml/artifacts/{model.pt,meta.json}. predict() returns top-3 KB
    targets with calibrated confidences plus a Grad-CAM grid."""

    def __init__(self, artifacts: Path, meta: dict | None = None):
        meta = meta or json.loads((artifacts / "meta.json").read_text())
        self.meta = meta
        self.version = meta["model_version"]
        self.classes: list[str] = meta["classes"]
        self.class_to_target: dict[str, str] = meta["class_to_target"]
        self.temperature: float = meta.get("temperature", 1.0)
        self.size: int = meta["img_size"]
        self.model = Net(meta["backbone"], len(self.classes), meta["head"], pretrained=False)
        state = torch.load(artifacts / "model.pt", map_location="cpu", weights_only=True)
        self.model.load_state_dict(state)
        self.model.train(False)  # inference mode: dropout off, batch-norm frozen
        self.tf = test_transform(self.size)

    def predict(self, img: Image.Image, k: int = 3) -> tuple[list[tuple[str, float]], dict]:
        x = self.tf(img.convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(x)[0]
        probs = torch.softmax(logits / self.temperature, dim=0).numpy()
        by_target: dict[str, float] = {}
        for cls, p in zip(self.classes, probs):
            t = self.class_to_target[cls]
            by_target[t] = by_target.get(t, 0.0) + float(p)
        ranked = sorted(by_target.items(), key=lambda kv: kv[1], reverse=True)[:k]
        top_class = int(np.argmax(probs))
        with torch.enable_grad():
            cam = gradcam(self.model, x.requires_grad_(True), top_class)
        return [(t, round(c, 4)) for t, c in ranked], {
            "grid": np.round(cam, 3).tolist(),
            "rows": cam.shape[0],
            "cols": cam.shape[1],
            "method": "grad-cam",
            "class": self.classes[top_class],
        }
