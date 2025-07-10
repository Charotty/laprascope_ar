# Модуль для расчёта точек троакаров и углов
# Здесь будут реализованы алгоритмы расчёта и анализа
import numpy as np


def calculate_trocar_points(mesh, anatomical_points, params=None):
    """
    Расчёт оптимальных точек троакаров на поверхности mesh.
    anatomical_points: dict с ключевыми анатомическими ориентирами (например, {'asis': [x,y,z], 'umbilicus': [x,y,z], ...})
    params: dict с параметрами (например, количество троакаров, минимальные расстояния и т.д.)
    Возвращает: список точек троакаров (N,3) и список углов (N,3)
    """
    # Пример: выбираем N точек, максимально удалённых друг от друга и от анатомических ориентиров
    N = params.get('num_ports', 3) if params else 3
    surface_points, _ = mesh.sample(N*10)
    trocar_points = []
    trocar_angles = []
    used = []
    for i in range(N):
        # Находим точку, максимально удалённую от уже выбранных и анатомических ориентиров
        dists = np.zeros(len(surface_points))
        for j, pt in enumerate(surface_points):
            d = 0
            for ap in anatomical_points.values():
                d += np.linalg.norm(pt - np.array(ap))
            for up in used:
                d += np.linalg.norm(pt - up)
            dists[j] = d
        idx = np.argmax(dists)
        trocar_points.append(surface_points[idx])
        used.append(surface_points[idx])
        # Пример: угол нормали к поверхности в этой точке
        normal = mesh.face_normals[mesh.nearest.face[idx]]
        trocar_angles.append(normal)
    return np.array(trocar_points), np.array(trocar_angles)
