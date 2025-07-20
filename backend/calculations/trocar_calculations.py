# Модуль для расчёта точек троакаров и углов
# Здесь будут реализованы алгоритмы расчёта и анализа
import numpy as np
import trimesh

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

    # 2. Оставляем точки c нормалью близкой к +Z
    z_axis = np.array([0, 0, 1.0])
    cos_thr = np.cos(np.deg2rad(max_angle_deg))
    keep_mask = (surface_normals @ z_axis) >= cos_thr
    candidate_pts = surface_points[keep_mask]
    candidate_normals = surface_normals[keep_mask]

    if len(candidate_pts) < num_ports:
        raise RuntimeError("Недостаточно кандидатных точек с подходящим углом нормали")

    trocar_points: list[np.ndarray] = []
    trocar_normals: list[np.ndarray] = []

    # 3. Greedy-подбор точек
    dist_ap = lambda pt: sum(np.linalg.norm(pt - ap) for ap in anatomical_points.values())

    for _ in range(num_ports):
        scores = []
        for idx, pt in enumerate(candidate_pts):
            # расстояние до анатомических + уже выбранных
            score = dist_ap(pt)
            for chosen in trocar_points:
                score += np.linalg.norm(pt - chosen)
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
