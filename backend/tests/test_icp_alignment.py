"""Phantom validation test for ICP alignment.

We generate a cube point cloud, apply a known rigid transform (translation 10,5,2 mm + small rotation),
then run align_icp and verify that RMSE error < 2 mm and translation difference < 5 mm (requirement).
"""
from pathlib import Path

import numpy as np

from backend.calculations.icp_alignment import align_icp


def _create_cube(side: float = 50.0, num: int = 1000) -> np.ndarray:
    """Create random points inside a cube centered at origin."""
    pts = (np.random.rand(num, 3) - 0.5) * side
    return pts.astype(np.float32)


def _apply_transform(pts: np.ndarray, R: np.ndarray, t: np.ndarray) -> np.ndarray:
    return (pts @ R.T) + t


def test_icp_alignment_accuracy() -> None:
    np.random.seed(42)
    src = _create_cube()

    # Ground-truth transform: small rotation + translation (mm)
    angle = np.deg2rad(5)
    Rz = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1],
    ], dtype=np.float32)
    t = np.array([10.0, 5.0, 2.0], dtype=np.float32)

    tgt = _apply_transform(src, Rz, t)

    T_est, src_aligned = align_icp(src, tgt, threshold=20.0)

    # Compute RMSE
    rmse = np.sqrt(np.mean(np.sum((src_aligned - tgt) ** 2, axis=1)))
    assert rmse < 2.0, f"RMSE too high: {rmse:.2f} mm"

    # Translation error
    est_t = T_est[:3, 3]
    trans_err = np.linalg.norm(est_t - t)
    assert trans_err < 5.0, f"Translation error {trans_err:.2f} mm exceeds 5 mm"
