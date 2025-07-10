# Модуль для импорта DICOM-серий из PACS (Orthanc/DICOMweb)
import os
import requests

def download_dicom_series_orthanc(orthanc_url, series_uid, out_dir, username=None, password=None):
    """
    Загружает DICOM-серию из Orthanc по SeriesInstanceUID через DICOMweb REST API.
    Сохраняет все файлы в out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)
    # Получаем список экземпляров (instances) в серии
    url = f"{orthanc_url}/series/{series_uid}/instances"
    auth = (username, password) if username and password else None
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    instances = r.json()
    for instance_id in instances:
        # Скачиваем сам DICOM-файл
        instance_url = f"{orthanc_url}/instances/{instance_id}/file"
        r = requests.get(instance_url, auth=auth)
        r.raise_for_status()
        out_path = os.path.join(out_dir, f"{instance_id}.dcm")
        with open(out_path, "wb") as f:
            f.write(r.content)
    return out_dir

