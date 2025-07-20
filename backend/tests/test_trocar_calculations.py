"""Unit-tests for trocar calculation heuristics."""

import numpy as np
import trimesh

from backend.calculations.trocar_calculations import calculate_trocar_points


def test_trocar_basic():
    """Ensure algorithm returns correct number of ports and respects min_distance."""
    mesh = trimesh.primitives.Sphere(radius=0.1)  # 10 cm sphere

    # Fake anatomical points: two points near +Z pole
    anatomical_points = {
        "asis_left": np.array([0.05, 0.0, 0.09]),
        "asis_right": np.array([-0.05, 0.0, 0.09]),
    }

    pts, norms = calculate_trocar_points(
        mesh,
        anatomical_points,
        num_ports=3,
        min_distance=0.04,
        max_angle_deg=45,
    )

    # Shapes
    assert pts.shape == (3, 3)
    assert norms.shape == (3, 3)

    # Distances between ports >= min_distance
    dists = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=-1)
    np.fill_diagonal(dists, 1.0)  # ignore self-dist
    assert (dists >= 0.04 - 1e-6).all()
