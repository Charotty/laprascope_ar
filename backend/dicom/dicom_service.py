"""dicom_service.py
====================
Общий сервис для работы с DICOM-данными. Содержит утилиты
для:
    • сохранения загруженных файлов во временную директорию;
    • поиска файлов одной серии (даже если в ZIP смешаны разные);
    • базовой валидации снимков;
    • конвертации серии в numpy-volume + метаданные.

Эти функции используются и веб-эндпоинтами (upload_dicom,
PACS-импорт), и тестами.
"""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pydicom
import SimpleITK as sitk
from pydicom.errors import InvalidDicomError

from backend.dicom.parser import find_dicom_series, extended_validate_dicom_file

__all__ = [
    "save_uploaded_files",
    "collect_series",
    "series_to_numpy",
]


TMP_ROOT = Path("data") / "dicom_samples"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def save_uploaded_files(files: List[Tuple[str, bytes]]) -> Path:
    """Сохраняет перечень (filename, raw_bytes) в уникальную папку.

    Возвращает путь к созданной директории.
    """
    target_dir = TMP_ROOT / f"upload_{uuid.uuid4().hex[:8]}"
    target_dir.mkdir(parents=True, exist_ok=True)
    for fname, raw in files:
        with open(target_dir / fname, "wb") as fp:
            fp.write(raw)
    return target_dir


# ---------------------------------------------------------------------------
# Series utilities
# ---------------------------------------------------------------------------

def collect_series(folder: os.PathLike) -> List[Path]:
    """Ищет все DICOM-файлы (рекурсивно) в *folder*.

    Возвращает список `Path` файлов одной серии. Если в директории
    обнаружены разные SeriesInstanceUID — будет выбрана самая большая по
    количеству файлов.
    """
    all_files = find_dicom_series(str(folder))
    if not all_files:
        raise FileNotFoundError("В папке не найдено DICOM-файлов")

    # Группируем по SeriesInstanceUID
    groups = {}
    for fp in all_files:
        try:
            ds = pydicom.dcmread(fp, stop_before_pixels=True)
        except InvalidDicomError:
            continue
        series_uid = ds.get("SeriesInstanceUID", "unknown")
        groups.setdefault(series_uid, []).append(Path(fp))

    # Берём самую большие группу
    series = max(groups.values(), key=len)
    # basic validation
    valid = [fp for fp in series if extended_validate_dicom_file(str(fp))[0]]
    if len(valid) < 3:
        raise ValueError("Недостаточно валидных файлов для построения серии")
    return valid


# ---------------------------------------------------------------------------
# ITK helpers
# ---------------------------------------------------------------------------

def series_to_numpy(series_files: List[Path]) -> Tuple[np.ndarray, Tuple[float, float, float]]:
    """Читает список файлов одной серии в 3-D numpy массив.

    Возвращает (volume[z,y,x], spacing(x,y,z)).
    """
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames([str(fp) for fp in series_files])
    img = reader.Execute()
    volume = sitk.GetArrayFromImage(img)  # (z, y, x)
    spacing = img.GetSpacing()  # (x, y, z)
    return volume, spacing
