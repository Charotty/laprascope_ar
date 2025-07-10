# Модуль для работы с DICOM-файлами
# Здесь будет реализован парсинг и базовая обработка DICOM

import pydicom
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from pydicom.data import get_testdata_file
from PIL import Image
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
import json
import logging
import glob

def read_dicom_info(filepath):
    """
    Читает DICOM-файл и выводит расширенные метаданные.
    """
    try:
        ds = pydicom.dcmread(filepath, force=True)
    except InvalidDicomError:
        print(f"Файл {filepath} не является DICOM.")
        return None
    print(f"\nФайл: {filepath}")
    # Выводим все стандартны�� метад������нные
    for elem in ds:
        if elem.VR != 'SQ':  # Не выводим вложенные последовательности
            print(f"{elem.tag} {elem.name}: {elem.value}")
    # Кратко выв��дим основные поля
    print(f"Пациент: {ds.get('PatientName', 'N/A')}")
    print(f"ID пациента: {ds.get('PatientID', 'N/A')}")
    print(f"Модальность: {ds.get('Modality', 'N/A')}")
    print(f"Размеры изображения: {ds.get('Rows', 'N/A')} x {ds.get('Columns', 'N/A')}")
    return ds

def save_dicom_image(ds, out_path):
    """
    Сохраняет изображение из DICOM-файла в PNG, если возможно.
    """
    if 'PixelData' not in ds:
        print("Нет данных изображения в DICOM-файле.")
        return False
    arr = ds.pixel_array
    # Приведение к 8-битному диапазону
    if arr.dtype != np.uint8:
        arr = (arr / arr.max() * 255).astype(np.uint8)
    img = Image.fromarray(arr)
    img.save(out_path)
    print(f"Изображение сохранено: {out_path}")
    return True

def select_dicom_folder():
    """
    Открывает диалог����вое окно для выбора папки с DICOM-файлами.
    """
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="Выберите папку с DICOM-файлами")
    return folder_selected

def is_dicom_file(filepath):
    """
    Проверяет, является ли файл DICOM (по сигнатуре).
    """
    try:
        with open(filepath, 'rb') as f:
            f.seek(128)
            magic = f.read(4)
            return magic == b'DICM'
    except Exception:
        return False

def find_dicom_files(folder):
    """
    Рекурсивно ищет все возможные DICOM-файлы (без расширения и с расширением) во всех подпапках.
    """
    dicom_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            filepath = os.path.join(root, file)
            # Пропускаем служебные файлы
            if file.lower() in ["dicomdir", "images.cds", "lex_img.cds", "protocols.cds", "protocol.pdf", "amimageviewer.exe"]:
                continue
            # Проверяем по сигнатуре DICOM
            if is_dicom_file(filepath):
                dicom_files.append(filepath)
    return dicom_files

def parse_dicomdir(dicomdir_path, base_folder=None):
    """
    Парсит DICOMDIR и возвращает список путей к DICOM-файлам серии.
    Если base_folder не указан, берёт папку DICOMDIR.
    """
    dicomdir = dcmread(dicomdir_path)
    if base_folder is None:
        base_folder = os.path.dirname(dicomdir_path)
    file_list = []
    for patient in dicomdir.patient_records:
        studies = patient.children
        for study in studies:
            series_list = study.children
            for series in series_list:
                images = series.children
                for image in images:
                    rel_path = image.ReferencedFileID
                    if isinstance(rel_path, (list, tuple)):
                        rel_path = os.path.join(*rel_path)
                    abs_path = os.path.join(base_folder, rel_path)
                    if os.path.exists(abs_path):
                        file_list.append(abs_path)
    return file_list

def find_dicom_series(folder):
    """
    Ищет все DICOM-файлы в папке, поддерживает DICOMDIR и вложенные папки.
    Возвращает список путей к DICOM-файлам.
    """
    dicom_files = []
    dicomdir_path = os.path.join(folder, "DICOMDIR")
    if os.path.exists(dicomdir_path):
        # Используем DICOMDIR для поиска файлов
        dicom_files = parse_dicomdir(dicomdir_path, base_folder=folder)
        return dicom_files
    # Если DICOMDIR нет, ищем как раньше
    import glob
    for ext in ("*.dcm", "*"):
        dicom_files.extend(glob.glob(os.path.join(folder, "**", ext), recursive=True))
    # Фильтрация по сигнатуре DICOM
    dicom_files = [f for f in dicom_files if is_dicom_file(f)]
    return dicom_files

def validate_dicom_file(filepath):
    """
    Проверяет корректность DICOM-файла (voxel spacing, ориентация, размер).
    Возвращает True/False и сообщение.
    """
    try:
        ds = pydicom.dcmread(filepath, stop_before_pixels=True)
        spacing = ds.get((0x0028, 0x0030), None)
        rows = ds.get((0x0028, 0x0010), None)
        cols = ds.get((0x0028, 0x0011), None)
        if not spacing or not rows or not cols:
            return False, "Отсутствуют ключевые параметры (spacing, rows, cols)"
        return True, "OK"
    except Exception as e:
        return False, str(e)

def extended_validate_dicom_file(filepath):
    """
    Расширенная валидация DICOM-файла:
    - Проверка наличия voxel spacing, rows, cols
    - Проверка корректности orientation (ImageOrientationPatient)
    - Проверка уникальности InstanceNumber
    - Проверка на повреждённость файла
    Возвращает (True/False, сообщение)
    """
    try:
        ds = pydicom.dcmread(filepath, stop_before_pixels=True)
        spacing = ds.get((0x0028, 0x0030), None)
        rows = ds.get((0x0028, 0x0010), None)
        cols = ds.get((0x0028, 0x0011), None)
        orientation = ds.get((0x0020, 0x0037), None)
        instance_number = ds.get((0x0020, 0x0013), None)
        if not spacing or not rows or not cols:
            return False, "Отсутствуют ключевые параметры (spacing, rows, cols)"
        if orientation is None or len(orientation) != 6:
            return False, "Некорректная ориента��ия (ImageOrientationPatient)"
        if instance_number is None:
            return False, "Нет InstanceNumber (номер среза)"
        return True, "OK"
    except Exception as e:
        return False, f"Ошибка чтения DICOM: {str(e)}"

def log_import_error(filepath, error_msg):
    """
    Логирует ошибку импорта DICOM в отдельный файл.
    """
    log_dir = os.path.join(os.path.dirname(__file__), '../../data/reports/errors')
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "dicom_import_errors.log"), "a", encoding="utf-8") as f:
        f.write(f"{filepath}: {error_msg}\n")

def extract_main_dicom_tags(ds):
    """
    Извлекает основные группы DICOM-меток из объекта Dataset.
    Возвращает словарь с ключевыми полями (все значения приводятся к строке для сериализации).
    """
    def safe_str(val):
        if isinstance(val, (list, tuple)):
            return [safe_str(v) for v in val]
        try:
            return str(val)
        except Exception:
            return ''
    tags = {
        # Информация о пациенте
        'PatientName': safe_str(ds.get((0x0010, 0x0010), '')),
        'PatientID': safe_str(ds.get((0x0010, 0x0020), '')),
        'PatientBirthDate': safe_str(ds.get((0x0010, 0x0030), '')),
        'PatientSex': safe_str(ds.get((0x0010, 0x0040), '')),
        'PatientAge': safe_str(ds.get((0x0010, 0x1010), '')),
        # Информация об исследовании
        'StudyInstanceUID': safe_str(ds.get((0x0020, 0x000D), '')),
        'StudyDate': safe_str(ds.get((0x0008, 0x0020), '')),
        'StudyTime': safe_str(ds.get((0x0008, 0x0030), '')),
        'StudyDescription': safe_str(ds.get((0x0008, 0x1030), '')),
        # Информация о серии
        'SeriesInstanceUID': safe_str(ds.get((0x0020, 0x000E), '')),
        'Modality': safe_str(ds.get((0x0008, 0x0060), '')),
        'SeriesNumber': safe_str(ds.get((0x0020, 0x0011), '')),
        'SeriesDescription': safe_str(ds.get((0x0008, 0x103E), '')),
        # Информация о снимке
        'SOPInstanceUID': safe_str(ds.get((0x0008, 0x0018), '')),
        'InstanceNumber': safe_str(ds.get((0x0020, 0x0013), '')),
        'Rows': safe_str(ds.get((0x0028, 0x0010), '')),
        'Columns': safe_str(ds.get((0x0028, 0x0011), '')),
        'PixelSpacing': safe_str(ds.get((0x0028, 0x0030), '')),
        # Информация об оборудовании
        'Manufacturer': safe_str(ds.get((0x0008, 0x0070), '')),
        'InstitutionName': safe_str(ds.get((0x0008, 0x0080), '')),
        'ManufacturerModelName': safe_str(ds.get((0x0008, 0x1090), '')),
        # Параметры сканирования
        'BodyPartExamined': safe_str(ds.get((0x0018, 0x0015), '')),
        'SliceThickness': safe_str(ds.get((0x0018, 0x0050), '')),
        'SpacingBetweenSlices': safe_str(ds.get((0x0018, 0x0088), '')),
        # Аннотации
        'ImageType': safe_str(ds.get((0x0008, 0x0008), '')),
    }
    return tags

def print_main_dicom_tags(tags):
    """
    Красиво выводит основные DICOM-теги.
    """
    print("\n--- Основные DICOM-метки ---")
    for k, v in tags.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    folder = select_dicom_folder()
    if not folder:
        print("Папка не выбрана.")
    else:
        print(f"Выбрана папка: {folder}")
        dicom_files = find_dicom_files(folder)
        print(f"Найдено DICOM-файлов: {len(dicom_files)}")
        all_tags = []
        for filepath in dicom_files:
            ds = read_dicom_info(filepath)
            if ds:
                tags = extract_main_dicom_tags(ds)
                print_main_dicom_tags(tags)
                all_tags.append({"filepath": filepath, "tags": tags})
                out_png = os.path.splitext(filepath)[0] + ".png"
                save_dicom_image(ds, out_png)
        # Выводим все собранные теги в формате JSON для отладки
        print("\n======= ВСЕ ТЕГИ В JSON =======")
        print(json.dumps(all_tags, ensure_ascii=False, indent=2))
        # С��храняем результат в отдельную папку с именем пациента
        import shutil
        # Имя па��иента = название папки выше (на��ример, Б��нникова)
        patient_name = os.path.basename(os.path.dirname(folder))
        out_dir = os.path.join(os.path.dirname(__file__), '../../data/reports', patient_name)
        os.makedirs(out_dir, exist_ok=True)
        out_json = os.path.join(out_dir, "dicom_tags_result.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(all_tags, f, ensure_ascii=False, indent=2)
        print(f"\nРезультат сохранён в фай��: {out_json}")
