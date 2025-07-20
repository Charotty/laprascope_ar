# backend/calculations/trocar_calculations.py — Trocar Port Placement

## Path & Summary
Heuristic algorithm to compute **N optimal trocar entry points** on a patient mesh, respecting spacing and angle constraints.

## Responsibilities
1. Compute surface normals and candidate points.
2. Filter by angle relative to patient Z-axis.
3. Greedy selection maximizing distance from anatomical landmarks & each other.
4. Ensure minimum inter-trocar distance.

## Key Functions
| Function | Purpose |
|----------|---------|
| `calculate_trocar_points(mesh, n_ports, min_dist, max_angle)` | Main API, returns list[Vector3] |
| `_filter_by_angle(verts, normals, max_angle)` | Exclude steep normals |
| `_greedy_select(candidates, min_dist, k)` | Picks `k` farthest points |

## Math Notes
* Uses `numpy.linalg.norm` for distances.
* Angle check via `cosθ = n·z`.

## Tests
`test_trocar_calculations.py` asserts:
* Correct number of ports.
* Pairwise distance ≥ `min_dist`.

## Dependencies
```
numpy, trimesh
```
