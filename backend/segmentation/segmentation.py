# Модуль для сегментации медицинских изображений
# Здесь будут реализованы алгоритмы сегментации и 3D-реконструкции

import os
import numpy as np
import SimpleITK as sitk
from skimage import measure
import trimesh

def load_dicom_series(dicom_folder):
    """
    Загружает серию DICOM в 3D-массив (numpy) и возвращает image, array, spacing, origin, direction
    """
    reader = sitk.ImageSeriesReader()
    series_IDs = reader.GetGDCMSeriesIDs(dicom_folder)
    if not series_IDs:
        raise FileNotFoundError(f"Нет DICOM-серий в папке: {dicom_folder}")
    series_file_names = reader.GetGDCMSeriesFileNames(dicom_folder, series_IDs[0])
    reader.SetFileNames(series_file_names)
    image = reader.Execute()
    array = sitk.GetArrayFromImage(image)  # (z, y, x)
    spacing = image.GetSpacing()           # (x, y, z)
    origin = image.GetOrigin()
    direction = image.GetDirection()
    return image, array, spacing, origin, direction

def simple_threshold_segmentation(array, threshold=(30, 300)):
    """
    Простая пороговая сегментация (например, для почки)
    Возвращает бинарную маску (numpy array)
    """
    mask = np.logical_and(array >= threshold[0], array <= threshold[1])
    return mask.astype(np.uint8)

def save_mask_nifti(mask, reference_image, out_path):
    """
    Сохраняет маску в формате NIfTI, используя reference_image для геометрии
    """
    mask_img = sitk.GetImageFromArray(mask)
    mask_img.CopyInformation(reference_image)
    sitk.WriteImage(mask_img, out_path)
    return out_path

def save_mask_png(mask, out_dir):
    """
    Сохраняет каждый срез маски как PNG в out_dir
    """
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    for i, slice_ in enumerate(mask):
        img = Image.fromarray((slice_ * 255).astype(np.uint8))
        img.save(os.path.join(out_dir, f"mask_{i:03d}.png"))

def mask_to_stl(mask, spacing, out_path):
    """
    Преобразует бинарную маску (3D numpy) в STL-модель через marching cubes
    """
    verts, faces, normals, values = measure.marching_cubes(mask, level=0.5, spacing=spacing)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals, process=True)
    mesh.export(out_path)
    return out_path

def mask_to_gltf(mask, spacing, out_path):
    """
    Преобразует бинарную маску (3D numpy) в GLTF-модель через marching cubes
    """
    verts, faces, normals, values = measure.marching_cubes(mask, level=0.5, spacing=spacing)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals, process=True)
    mesh.export(out_path)
    return out_path

def segment_and_export(dicom_folder, out_dir, threshold=(30, 300)):
    """
    Полный пайплайн: загрузка DICOM, сегментация, экспорт маски (NIfTI, PNG)
    """
    image, array, spacing, origin, direction = load_dicom_series(dicom_folder)
    mask = simple_threshold_segmentation(array, threshold)
    os.makedirs(out_dir, exist_ok=True)
    nifti_path = os.path.join(out_dir, "mask.nii.gz")
    save_mask_nifti(mask, image, nifti_path)
    save_mask_png(mask, os.path.join(out_dir, "mask_png"))
    return nifti_path

def segment_and_export_full(dicom_folder, out_dir, threshold=(30, 300)):
    """
    Полный пайплайн: загрузка DICOM, сегментация, экспорт маски (NIfTI, PNG), STL, GLTF
    """
    image, array, spacing, origin, direction = load_dicom_series(dicom_folder)
    mask = simple_threshold_segmentation(array, threshold)
    os.makedirs(out_dir, exist_ok=True)
    nifti_path = os.path.join(out_dir, "mask.nii.gz")
    save_mask_nifti(mask, image, nifti_path)
    save_mask_png(mask, os.path.join(out_dir, "mask_png"))
    stl_path = os.path.join(out_dir, "mask.stl")
    mask_to_stl(mask, spacing, stl_path)
    gltf_path = os.path.join(out_dir, "mask.glb")
    mask_to_gltf(mask, spacing, gltf_path)
    return {
        "nifti": nifti_path,
        "stl": stl_path,
        "gltf": gltf_path,
        "mask_png_dir": os.path.join(out_dir, "mask_png")
    }
