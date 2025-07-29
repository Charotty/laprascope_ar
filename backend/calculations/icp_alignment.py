"""ICP alignment utilities using Open3D.

Functions:
    align_icp(source_pts: np.ndarray, target_pts: np.ndarray) -> Tuple[np.ndarray, np.ndarray]
        Returns 4×4 transformation matrix and transformed source points.

Used for C2: aligning skin surface (patient point cloud) to model-derived point cloud.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import open3d as o3d

__all__ = ["align_icp"]


def _to_pcd(points: np.ndarray) -> o3d.geometry.PointCloud:
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))
    return pcd


def align_icp(source_pts: np.ndarray, target_pts: np.ndarray, threshold: float = 10.0) -> Tuple[np.ndarray, np.ndarray]:
    """Rigid ICP alignment (point-to-point)."""
    assert source_pts.shape[1] == 3 and target_pts.shape[1] == 3, "pts must be Nx3"

    src_pcd = _to_pcd(source_pts)
    tgt_pcd = _to_pcd(target_pts)

    trans_init = np.eye(4)
    reg = o3d.pipelines.registration.registration_icp(
        src_pcd,
        tgt_pcd,
        threshold,
        trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=50),
    )

    transformed = reg.transformation @ np.concatenate([source_pts.T, np.ones((1, source_pts.shape[0]))], axis=0)
    return reg.transformation.astype(np.float32), transformed[:3].T
