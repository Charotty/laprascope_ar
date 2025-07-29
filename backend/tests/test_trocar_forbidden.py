import numpy as np
import trimesh
from backend.calculations.trocar_calculations import calculate_trocar_points

def _plane_mesh():
    verts = [[-0.5, -0.5, 0], [0.5, -0.5, 0], [0.5, 0.5, 0], [-0.5, 0.5, 0]]
    faces = [[0, 1, 2], [0, 2, 3]]
    return trimesh.Trimesh(verts, faces)

def _sphere_mesh(center=(0, 0, 0.05), radius=0.1, count=3):
    return trimesh.creation.icosphere(subdivisions=2, radius=radius).apply_translation(center)

def test_forbidden_zone_skip():
    plane = _plane_mesh()
    liver = _sphere_mesh()
    anatomical = {}
    pts, _ = calculate_trocar_points(
        plane,
        anatomical,
        num_ports=1,
        forbidden_meshes=[liver],
    )
    # Point should be above radius distance from liver center
    dist = np.linalg.norm(pts[0] - np.array([0, 0, 0.05]))
    assert dist > 0.11
