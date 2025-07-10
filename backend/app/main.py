from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
import os
import tempfile
import numpy as np
from backend.models.model_handler import load_stl_model, get_mesh_surface_points, export_points_json
from backend.calculations.trocar_calculations import calculate_trocar_points
from backend.segmentation.segmentation import segment_and_export, segment_and_export_full
from backend.dicom.pacs_import import download_dicom_series_orthanc
from backend.dicom.parser import find_dicom_series, extended_validate_dicom_file, log_import_error
import datetime

app = FastAPI()

@app.post("/upload_stl/")
def upload_stl(stl: UploadFile = File(...), anatomical_points: str = Form("{}"), num_ports: int = Form(3)):
    """
    Загружает STL, получает анатомические точки (JSON-строка), считает точки троакаров, возвращает их в JSON
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        stl_path = os.path.join(tmpdir, stl.filename)
        with open(stl_path, "wb") as f:
            f.write(stl.file.read())
        mesh = load_stl_model(stl_path)
        # anatomical_points: JSON-строка вида {"asis": [x,y,z], ...}
        import json
        anatomical_points_dict = json.loads(anatomical_points)
        trocar_points, trocar_angles = calculate_trocar_points(mesh, anatomical_points_dict, params={"num_ports": num_ports})
        # Экспортируем результат во временный JSON
        out_json = os.path.join(tmpdir, "trocar_points.json")
        export_points_json(trocar_points, out_json)
        # Возвращаем результат
        return JSONResponse({
            "trocar_points": trocar_points.tolist(),
            "trocar_angles": trocar_angles.tolist(),
            "message": "Расчёт выполнен успешно"
        })

@app.get("/test_stl_points/")
def test_stl_points():
    """
    Тестовый endpoint: грузит example_model.stl, считает 3 точки на поверхности, возвращает их
    """
    stl_path = os.path.join(os.path.dirname(__file__), '../../data/models/example_model.stl')
    mesh = load_stl_model(stl_path)
    points = get_mesh_surface_points(mesh, sample_count=3)
    return JSONResponse({"points": points.tolist()})

@app.post("/segment_dicom/")
def segment_dicom(dicom_folder: str = Form(...), threshold_min: int = Form(30), threshold_max: int = Form(300)):
    """
    Запуск сегментации: принимает путь к папке с DICOM, пороги, возвращает путь к маске (NIfTI)
    """
    import uuid
    out_dir = os.path.join("data", "reports", f"segmentation_{uuid.uuid4().hex[:8]}")
    os.makedirs(out_dir, exist_ok=True)
    try:
        nifti_path = segment_and_export(dicom_folder, out_dir, threshold=(threshold_min, threshold_max))
        return JSONResponse({
            "nifti_mask_path": nifti_path,
            "mask_png_dir": os.path.join(out_dir, "mask_png"),
            "message": "Сегментация выполнена успешно"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/segment_dicom_full/")
def segment_dicom_full(dicom_folder: str = Form(...), threshold_min: int = Form(30), threshold_max: int = Form(300)):
    """
    Запуск полного пайплайна сегментации: принимает путь к папке с DICOM, пороги, возвращает пути к маске (NIfTI), STL, GLTF, PNG
    """
    import uuid
    out_dir = os.path.join("data", "reports", f"segmentation_{uuid.uuid4().hex[:8]}")
    os.makedirs(out_dir, exist_ok=True)
    try:
        result = segment_and_export_full(dicom_folder, out_dir, threshold=(threshold_min, threshold_max))
        return JSONResponse({
            "nifti_mask_path": result["nifti"],
            "stl_path": result["stl"],
            "gltf_path": result["gltf"],
            "mask_png_dir": result["mask_png_dir"],
            "message": "Сегментация и экспорт выполнены успешно"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/import_and_validate_pacs/")
def import_and_validate_pacs(
    orthanc_url: str = Form(...),
    series_uid: str = Form(...),
    username: str = Form(None),
    password: str = Form(None)
):
    """
    Импортирует DICOM-серию из PACS (Orthanc), валидирует все файлы, логирует ошибки, возвращает список валидных файлов
    """
    import uuid
    out_dir = os.path.join("data", "dicom_samples", f"pacs_import_{uuid.uuid4().hex[:8]}")
    try:
        download_dicom_series_orthanc(orthanc_url, series_uid, out_dir, username, password)
        dicom_files = find_dicom_series(out_dir)
        valid_files = []
        for f in dicom_files:
            ok, msg = extended_validate_dicom_file(f)
            if ok:
                valid_files.append(f)
            else:
                log_import_error(f, msg)
        return JSONResponse({
            "import_dir": out_dir,
            "valid_dicom_files": valid_files,
            "invalid_count": len(dicom_files) - len(valid_files),
            "message": "Импорт и валидация завершены"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/import_segment_pacs/")
def import_segment_pacs(
    orthanc_url: str = Form(...),
    series_uid: str = Form(...),
    username: str = Form(None),
    password: str = Form(None),
    threshold_min: int = Form(30),
    threshold_max: int = Form(300)
):
    """
    Импортирует DICOM-серию из PACS (Orthanc), валидирует, сегментирует и экспортирует маску и 3D-модель.
    Возвращает пути к результатам.
    """
    import uuid
    from backend.segmentation.segmentation import segment_and_export_full
    out_dir = os.path.join("data", "dicom_samples", f"pacs_import_{uuid.uuid4().hex[:8]}")
    try:
        # 1. Импорт из PACS
        download_dicom_series_orthanc(orthanc_url, series_uid, out_dir, username, password)
        # 2. Валидация
        dicom_files = find_dicom_series(out_dir)
        valid_files = []
        for f in dicom_files:
            ok, msg = extended_validate_dicom_file(f)
            if ok:
                valid_files.append(f)
            else:
                log_import_error(f, msg)
        if not valid_files:
            return JSONResponse(status_code=400, content={"detail": "Нет валидных DICOM-файлов для сегментации"})
        # 3. Сегментация и экспорт (используем папку с валидными файлами)
        segm_out_dir = os.path.join("data", "reports", f"segmentation_{uuid.uuid4().hex[:8]}")
        os.makedirs(segm_out_dir, exist_ok=True)
        # Для простоты передаём папку, где лежат только валидные файлы
        # Можно скопиров��ть валидные файлы во временную папку, если нужно
        import shutil
        temp_valid_dir = os.path.join(segm_out_dir, "valid_dicom")
        os.makedirs(temp_valid_dir, exist_ok=True)
        for f in valid_files:
            shutil.copy2(f, temp_valid_dir)
        result = segment_and_export_full(temp_valid_dir, segm_out_dir, threshold=(threshold_min, threshold_max))
        return JSONResponse({
            "nifti_mask_path": result["nifti"],
            "stl_path": result["stl"],
            "gltf_path": result["gltf"],
            "mask_png_dir": result["mask_png_dir"],
            "import_dir": out_dir,
            "valid_dicom_files": valid_files,
            "invalid_count": len(dicom_files) - len(valid_files),
            "message": "Импорт, валидация и сегментация завершены"
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик ошибок: сохраняет ошибку в фай�� и возвращае�� JSON с ошибкой
    """
    error_dir = os.path.join(os.path.dirname(__file__), '../../data/reports/errors')
    os.makedirs(error_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    error_file = os.path.join(error_dir, f"fastapi_error_{timestamp}.log")
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(f"URL: {request.url}\n")
        f.write(f"Method: {request.method}\n")
        f.write(f"Exception: {repr(exc)}\n")
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error_file": error_file})
