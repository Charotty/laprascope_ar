# Модуль для работы с 3D-моделями
# Здесь будет реализована загрузка, сохранение и конвертация моделей

import trimesh
import numpy as np
import json
import os


def load_stl_model(stl_path):
    """
    Загружает STL-модель и возвращает объект trimesh.Trimesh
    """
    mesh = trimesh.load_mesh(stl_path)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("STL-файл не содержит корректную 3D-модель.")
    return mesh


def get_mesh_surface_points(mesh, sample_count=1000):
    """
    Возвращает sample_count случайных точек на поверхности mesh (np.ndarray shape=(N,3))
    """
    points, _ = trimesh.sample.sample_surface(mesh, sample_count)
    return points


def export_points_json(points, out_path):
    """
    Сохраняет массив точек (N,3) в JSON-файл
    """
    data = {"points": points.tolist()}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path


def visualize_points_on_mesh(mesh, points, out_path=None):
    """
    Визуализирует mesh с точками (использует matplotlib, сохраняет PNG если out_path)
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    mesh.show(ax=ax)
    pts = np.array(points)
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c='r', s=20)
    if out_path:
        plt.savefig(out_path)
    else:
        plt.show()
    plt.close(fig)
