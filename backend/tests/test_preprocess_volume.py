"""Tests for preprocess_volume.py using synthetic data."""

from pathlib import Path

import numpy as np
import SimpleITK as sitk

from backend.dataset_tools.preprocess_volume import (
    TARGET_SPACING,
    normalize_hu,
    resample_isotropic,
)


def _make_synthetic_image(size=(64, 64, 64), spacing=(2.0, 2.0, 2.0)) -> sitk.Image:
    arr = np.random.randint(-200, 500, size, dtype=np.int16)
    img = sitk.GetImageFromArray(arr)
    img.SetSpacing(spacing)
    return img


def test_resample_isotropic() -> None:
    img = _make_synthetic_image()
    iso = resample_isotropic(img, TARGET_SPACING)
    assert all(abs(a - b) < 1e-6 for a, b in zip(iso.GetSpacing(), TARGET_SPACING)), "Spacing not isotropic"


def test_normalize_hu() -> None:
    arr = np.array([-200, -100, 0, 200, 400, 600], dtype=np.int16)
    norm = normalize_hu(arr)
    assert norm.min() >= 0 and norm.max() <= 1, "Normalization out of bounds"
    # Values below HU_MIN should clip to 0
    assert norm[0] == 0.0
    # Values above HU_MAX should clip to 1
    assert norm[-1] == 1.0
