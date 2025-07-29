# backend/calculations/trocar_calculations.py — Trocar Port Placement

## Path & Summary
Heuristic algorithm to compute **N optimal trocar entry points** on a patient mesh, respecting spacing and angle constraints.

## Responsibilities
1. Compute surface normals and candidate points.
2. Filter by angle relative to **computed outward axis** (patient pose + table tilt).
3. Greedy scoring with weighted terms: distance to landmarks/ports, **tool length to target point**, **angle to target**, collision-free.
4. Ensure minimum inter-trocar distance.

## Key API
`calculate_trocar_points( mesh,
                          anatomical_points: dict,
                          num_ports: int = 3,
                          min_distance: float = 0.04,
                          max_angle_deg: float = 30,
                          patient_position: str = "supine",
                          table_pitch_deg: float = 0,
                          table_roll_deg: float = 0,
                          target_point: np.ndarray | None = None,
                          forbidden_meshes: list[trimesh.Trimesh] | None = None,
                          w_dist=1.0, w_len=1.0, w_angle=0.5) -> (pts, normals)`

| Parameter | Description |
|-----------|-------------|
| `patient_position` | `supine/prone/left/right` – базовый вектор «наружу» |
| `table_pitch_deg`,`table_roll_deg` | Наклон стола (°) |
| `target_point` | Точка цели (центр почки) для минимизации длины инструмента |
| `forbidden_meshes` | Меши органов, пересечение с которыми запрещено |
| `w_*` | Веса в скоринговой функции |

### Алгоритм лучевой проверки
Для каждого кандидата испускается луч по нормали. `trimesh.ray.intersects_any` отбрасывает точку, если луч пересекает любую ``forbidden_mesh``.

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
