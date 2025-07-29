# Модуль для расчёта точек троакаров и углов
# Здесь будут реализованы алгоритмы расчёта и анализа
import numpy as np
import trimesh
from math import radians, cos, sin
from typing import Sequence

# ------------------------------------------------------------
#  Helper orientation utilities
# ------------------------------------------------------------

def _rotation_matrix(pitch_deg: float = 0.0, roll_deg: float = 0.0) -> np.ndarray:
    """Return 3×3 rotation matrix for given pitch (around X) and roll (around Y) in degrees."""
    pitch = radians(pitch_deg)
    roll = radians(roll_deg)
    Rx = np.array(
        [[1, 0, 0], [0, cos(pitch), -sin(pitch)], [0, sin(pitch), cos(pitch)]],
        dtype=float,
    )
    Ry = np.array(
        [[cos(roll), 0, sin(roll)], [0, 1, 0], [-sin(roll), 0, cos(roll)]],
        dtype=float,
    )
    # Apply pitch then roll (order Y*X)
    return Ry @ Rx

def _base_outward_vector(patient_position: str) -> np.ndarray:
    """Return canonical outward vector for patient position.

    supine  – lying on back   → +Z (0,0,1)
    prone   – lying on belly  → -Z (0,0,-1)
    left    – lying on left   → -X (-1,0,0)
    right   – lying on right  → +X (1,0,0)
    """
    mapping = {
        "supine": np.array([0, 0, 1.0]),
        "prone": np.array([0, 0, -1.0]),
        "left": np.array([-1.0, 0, 0]),
        "right": np.array([1.0, 0, 0]),
    }
    if patient_position not in mapping:
        raise ValueError("patient_position must be one of: " + ", ".join(mapping))
    return mapping[patient_position]

def _compute_outward_vector(patient_position: str, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """Compute final outward vector after table tilt rotations."""
    base = _base_outward_vector(patient_position)
    R = _rotation_matrix(pitch_deg, roll_deg)
    return R @ base

# ------------------------------------------------------------
#  Public API
# ------------------------------------------------------------

def calculate_trocar_points(
    mesh: trimesh.Trimesh,
    anatomical_points: dict[str, np.ndarray],
    *,
    num_ports: int = 3,
    min_distance: float = 0.04,
    max_angle_deg: float = 30,
    patient_position: str = "supine",
    table_pitch_deg: float = 0.0,
    table_roll_deg: float = 0.0,
    target_point: np.ndarray | None = None,
    w_dist: float = 1.0,
    w_len: float = 1.0,
    w_angle: float = 0.5,
    forbidden_meshes: Sequence[trimesh.Trimesh] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Подбор оптимальных точек введения троакаров.

    Алгоритм (простая эвристика для MVP):
    1. Сэмплируем 5× больше точек, чем нужно, на поверхности *mesh*.
    2. Отбрасываем точки, чья нормаль отклонена от оси Z (пациент «лежа») > *max_angle_deg*.
    3. Итерируемся, выбирая точку, максимально удалённую от уже выбранных *и* всех анатомических ориентиров.
       При выборе также проверяем минимум расстояния `min_distance` (м).
    4. Для каждой конечной точки возвращаем вектор нормали (для ориентации инструмента).

    Параметры
    ----------
    mesh : trimesh.Trimesh
        Трёхмерная сетка поверхности (обычно пациенты + кожа).
    anatomical_points : dict[str, np.ndarray]
        Ключевые ориентиры (ASIS, пупок и т.д.), в мировых координатах.
    num_ports : int
        Требуемое количество портов.
    min_distance : float
        Минимальное допустимое расстояние между портами, метры.
    max_angle_deg : float
        Предельно допустимое отклонение нормали от оси Z (deg).
    patient_position : str
        Положение пациента (supine, prone, left, right).
    table_pitch_deg : float
        Угол наклона операционной таблицы (deg).
    table_roll_deg : float
        Угол наклона операционной таблицы (deg).
    target_point : np.ndarray | None
        Целевая точка для ориентации троакаров.
    w_dist : float
        Вес расстояния между портами/ориентирами (чем больше, тем шире порт).
    w_len : float
        Вес длины инструмента (приоритет ближе к target_point).
    w_angle : float
        Вес угла между нормалью и направлением к target_point.
    forbidden_meshes : list[trimesh.Trimesh] | None
        Меш-модели органов, пересечение с лучом которых недопустимо.

    Returns
    -------
    trocar_points : (N,3) np.ndarray
    trocar_normals : (N,3) np.ndarray
    """

    if num_ports < 1:
        raise ValueError("num_ports must be >=1")

    # 1. Сэмплируем достаточное количество точек
    sample_count = num_ports * 10
    surface_points, face_ids = mesh.sample(sample_count, return_index=True)
    surface_normals = mesh.face_normals[face_ids]

    # 2. Оставляем точки c нормалью близкой к outward
    outward_axis = _compute_outward_vector(patient_position, table_pitch_deg, table_roll_deg)
    outward_axis = outward_axis / np.linalg.norm(outward_axis)
    cos_thr = np.cos(np.deg2rad(max_angle_deg))
    keep_mask = (surface_normals @ outward_axis) >= cos_thr
    candidate_pts = surface_points[keep_mask]
    candidate_normals = surface_normals[keep_mask]

    if len(candidate_pts) < num_ports:
        raise RuntimeError("Недостаточно кандидатных точек с подходящим углом нормали")

    trocar_points: list[np.ndarray] = []
    trocar_normals: list[np.ndarray] = []

    def _distance_score(pt: np.ndarray) -> float:
        return sum(np.linalg.norm(pt - ap) for ap in anatomical_points.values())

    # 3. Greedy-подбор точек
    for _ in range(num_ports):
        scores = []
        for idx, pt in enumerate(candidate_pts):
            # Основной скоринг
            score = w_dist * _distance_score(pt)
            for chosen in trocar_points:
                score += w_dist * np.linalg.norm(pt - chosen)

            if target_point is not None:
                vec_to_target = target_point - pt
                dist_len = np.linalg.norm(vec_to_target)
                score -= w_len * dist_len  # ближе = лучше (+score за счёт -dist)
                if dist_len > 0:
                    vec_to_target /= dist_len
                    angle = np.arccos(np.clip(vec_to_target @ candidate_normals[idx] / (np.linalg.norm(candidate_normals[idx]) + 1e-6), -1, 1))
                    score -= w_angle * angle  # меньший угол → лучше

            # Forbidden zone check: skip early if ray intersects any forbidden mesh
            if forbidden_meshes:
                ray_orig = pt + candidate_normals[idx] * 1e-3  # slight offset outward
                ray_dir = candidate_normals[idx]
                try:
                    if any(m.ray.intersects_any(ray_orig[None, :], ray_dir[None, :]) for m in forbidden_meshes):
                        scores.append(-np.inf)
                        continue
                except Exception:
                    pass  # fallback if ray module unavailable

            scores.append(score)

        best_idx = int(np.argmax(scores))
        best_pt = candidate_pts[best_idx]
        best_n = candidate_normals[best_idx]

        # Проверяем min_distance к уже выбранным
        if any(np.linalg.norm(best_pt - p) < min_distance for p in trocar_points):
            # Удаляем точку из кандидатов и продолжаем
            candidate_pts = np.delete(candidate_pts, best_idx, axis=0)
            candidate_normals = np.delete(candidate_normals, best_idx, axis=0)
            continue

        trocar_points.append(best_pt)
        trocar_normals.append(best_n)

        # Удаляем точки, которые стали слишком близко
        keep = [np.linalg.norm(pt - best_pt) >= min_distance for pt in candidate_pts]
        candidate_pts = candidate_pts[keep]
        candidate_normals = candidate_normals[keep]

        if len(candidate_pts) == 0 and len(trocar_points) < num_ports:
            raise RuntimeError("Не удалось найти достаточно точек, удовлетворяющих min_distance")

    return np.stack(trocar_points), np.stack(trocar_normals)
