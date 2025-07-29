"""Pre-process a DICOM series into a normalized NumPy volume.

Steps:
1. Read DICOM series with SimpleITK.
2. Resample to isotropic 1 mm spacing.
3. Clip HU to [-100, 400].
4. Normalize to [0, 1] float32.
5. Save to .npy or .nii.gz depending on --output path.

Example:
    python preprocess_volume.py \
        --input C:\data\anon_dicom \
        --output C:\data\volumes\patient001.npy
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple

import numpy as np
import SimpleITK as sitk

HU_MIN = -100
HU_MAX = 400
TARGET_SPACING = (1.0, 1.0, 1.0)  # (z, y, x) mm

def read_sitk_image(dcm_dir: Path) -> sitk.Image:
    reader = sitk.ImageSeriesReader()
    series = reader.GetGDCMSeriesFileNames(str(dcm_dir))
    if not series:
        raise ValueError(f"No DICOM files detected in {dcm_dir}")
    reader.SetFileNames(series)
    image = reader.Execute()
    return image


def resample_isotropic(img: sitk.Image, spacing: Tuple[float, float, float]) -> sitk.Image:
    original_spacing = img.GetSpacing()
    if np.allclose(original_spacing, spacing):
        return img
    original_size = img.GetSize()
    new_size = [
        int(round(osz * ospc / nspc))
        for osz, ospc, nspc in zip(original_size, original_spacing, spacing)
    ]
    resample = sitk.ResampleImageFilter()
    resample.SetOutputSpacing(spacing)
    resample.SetSize(new_size)
    resample.SetOutputDirection(img.GetDirection())
    resample.SetOutputOrigin(img.GetOrigin())
    resample.SetInterpolator(sitk.sitkLinear)
    return resample.Execute(img)


def sitk_to_numpy(img: sitk.Image) -> np.ndarray:
    # Convert to numpy array (z, y, x) order
    arr = sitk.GetArrayFromImage(img).astype(np.int16)
    return arr


def normalize_hu(arr: np.ndarray) -> np.ndarray:
    arr = np.clip(arr, HU_MIN, HU_MAX)
    arr = (arr - HU_MIN) / (HU_MAX - HU_MIN)
    return arr.astype(np.float32)


def preprocess_series(input_dir: Path) -> np.ndarray:
    img = read_sitk_image(input_dir)
    img = resample_isotropic(img, TARGET_SPACING)
    arr = sitk_to_numpy(img)
    arr = normalize_hu(arr)
    return arr


def save_volume(arr: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".npy":
        np.save(output_path, arr)
    else:
        # if .nii or .nii.gz, wrap back to sitk Image
        img = sitk.GetImageFromArray(arr)
        sitk.WriteImage(img, str(output_path))


def parse_args():
    p = argparse.ArgumentParser(description="Pre-process DICOM series → NumPy volume")
    p.add_argument("--input", "-i", type=Path, required=True, help="Folder with anonymized DICOM series")
    p.add_argument("--output", "-o", type=Path, required=True, help="Output .npy or .nii.gz file")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    volume = preprocess_series(args.input)
    save_volume(volume, args.output)
    print("Saved pre-processed volume →", args.output)


if __name__ == "__main__":
    main()
