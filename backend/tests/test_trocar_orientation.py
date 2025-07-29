import numpy as np
import trimesh
from backend.calculations.trocar_calculations import calculate_trocar_points

def _make_plane(size=0.4, z=0.0):
    """Return a square plane mesh centered at origin pointing +Z"""
    half = size / 2
    vertices = [
        [-half, -half, z],
        [half, -half, z],
        [half, half, z],
        [-half, half, z],
    ]
    faces = [[0, 1, 2], [0, 2, 3]]
    return trimesh.Trimesh(vertices=vertices, faces=faces)

def test_orientation_supine_vs_left():
    mesh = _make_plane()
    anatomical = {"umbilicus": np.array([0, 0, 0.05])}

    # Supine default, expect normal +Z accepted
    pts_sup, _ = calculate_trocar_points(mesh, anatomical, num_ports=1)
    assert pts_sup.shape == (1, 3)

    # Patient lying on left side: outward should be -X, rotate plane accordingly
    mesh_left = mesh.copy()
    mesh_left.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
    pts_left, _ = calculate_trocar_points(mesh_left, anatomical, num_ports=1, patient_position="left")
    assert pts_left.shape == (1, 3)

    # Points should be different positions (side change)
    assert not np.allclose(pts_sup, pts_left)

def test_table_tilt_pitch():
    mesh = _make_plane()
    anatomical = {}
    # Tilt table 30 deg, still should find point
    pts, _ = calculate_trocar_points(mesh, anatomical, num_ports=1, table_pitch_deg=30)
    assert pts.shape == (1, 3)
