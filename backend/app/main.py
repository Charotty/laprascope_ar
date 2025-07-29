from fastapi import FastAPI, UploadFile, File, Form, Request, Body, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
from backend.models.model_handler import load_stl_model, get_mesh_surface_points, export_points_json
from backend.calculations.trocar_calculations import calculate_trocar_points
from backend.segmentation.segmentation import segment_and_export, segment_and_export_full, EmptyMaskError
from backend.dicom.pacs_import import download_dicom_series_orthanc
from backend.dicom.parser import find_dicom_series, extended_validate_dicom_file, log_import_error
from backend.dicom import dicom_service
import datetime

# In-memory simple task registry for async jobs (MVP, not for production)
from typing import Dict, List
import uuid as _uuid
_tasks: Dict[str, Dict] = {}

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload_stl/")
def upload_stl(
    stl: UploadFile = File(...),
    anatomical_points: str = Form("{}"),
    num_ports: int = Form(3),
    patient_position: str = Form("supine"),
    table_pitch_deg: float = Form(0.0),
    table_roll_deg: float = Form(0.0),
    forbidden_mesh_paths: str = Form("[]"),
):
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
        import trimesh
        forb_paths = json.loads(forbidden_mesh_paths)
        forbidden_meshes = []
        for p in forb_paths:
            if os.path.exists(p):
                try:
                    forbidden_meshes.append(trimesh.load(p, force='mesh'))
                except Exception:
                    pass

        trocar_points, trocar_angles = calculate_trocar_points(
            mesh,
            anatomical_points_dict,
            num_ports=num_ports,
            patient_position=patient_position,
            table_pitch_deg=table_pitch_deg,
            table_roll_deg=table_roll_deg,
            forbidden_meshes=forbidden_meshes,
        )
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
    except EmptyMaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    except EmptyMaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
        # 1. Импорт из PACС
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
        # Можно скопиров��ть в��лидные файлы во временную папку, если нужно
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

@app.post("/export/report/")
def export_report(request: Request):
    """
    Заглушка: экспорт PDF-отчёта, PNG-скриншотов, логов (JSON/CSV)
    Принимает параметры через JSON body (например, patient_id, options)
    Возвращает путь к файлу или ссылку (заглушка)
    """
    try:
        data = request.json() if hasattr(request, 'json') else {}
    except Exception:
        data = {}
    # TODO: вызвать генератор отчёта, собрать PNG, логи и PDF
    return JSONResponse({
        "status": "ok",
        "report_path": "/path/to/report.pdf",
        "log_path": "/path/to/log.json",
        "png_path": "/path/to/screenshot.png"
    })

@app.post("/log/")
def log_user_action(request: Request):
    """
    Заглушка: логирование действий пользователя (например, корректировка, экспорт, просмотр)
    Принимает JSON с описанием действия
    """
    try:
        data = request.json() if hasattr(request, 'json') else {}
    except Exception:
        data = {}
    # TODO: сохранить лог в файл или БД
    return JSONResponse({"status": "logged", "action": data})

@app.post("/unity/upload/")
def unity_upload(file: UploadFile = File(...), meta: str = Form("{}")):
    """
    Заглушка: загрузка моделей, масок, отчётов из Unity
    """
    # TODO: сохранить файл и метаданные
    return JSONResponse({"status": "uploaded", "filename": file.filename})

@app.get("/unity/download/")
def unity_download(filename: str):
    """
    Заглушка: скачивание моделей, масок, отчётов для Unity
    """
    # TODO: реализовать выдачу файла
    return JSONResponse({"status": "ready", "filename": filename})

@app.post("/anatomical_points/")
def save_anatomical_points(patient_id: str = Form(...), points: str = Form(...)):
    """
    Принимает и сохраняет анатомические точки для пациент��.
    points — JSON-строка вида {"asis": [x, y, z], "umbilicus": [x, y, z], ...}
    """
    import json
    out_dir = os.path.join("data", "reports", patient_id)
    os.makedirs(out_dir, exist_ok=True)
    points_path = os.path.join(out_dir, "anatomical_points.json")
    with open(points_path, "w", encoding="utf-8") as f:
        f.write(points)
    return JSONResponse({"status": "ok", "points_path": points_path})

@app.get("/anatomical_points/")
def get_anatomical_points(patient_id: str):
    """
    Возвращает сохранённые анатомические точки для пациента.
    """
    points_path = os.path.join("data", "reports", patient_id, "anatomical_points.json")
    if not os.path.exists(points_path):
        return JSONResponse(status_code=404, content={"detail": "Points not found"})
    with open(points_path, "r", encoding="utf-8") as f:
        points = f.read()
    return JSONResponse({"points": points})

@app.post("/anatomical_cs/")
def build_anatomical_cs(patient_id: str = Form(...)):
    """
    Строит анатомическую координатную систему по сохранённым точкам пациента.
    Возвращает параметры системы координа�� (заглушка).
    """
    # TODO: реализовать построение координатной системы
    # Сейчас возвращает заглушку
    return JSONResponse({
        "status": "ok",
        "origin": [0, 0, 0],
        "axes": {
            "x": [1, 0, 0],
            "y": [0, 1, 0],
            "z": [0, 0, 1]
        }
    })

@app.post("/segment_dicom_async/")
async def segment_dicom_async(
    background_tasks: BackgroundTasks,
    dicom_folder: str = Form(...),
    threshold_min: int = Form(30),
    threshold_max: int = Form(300),
):
    """Запускает сегментацию в фоне и возвращает task_id."""
    task_id = _uuid.uuid4().hex[:8]
    _tasks[task_id] = {"status": "pending"}

    def _run():
        try:
            out_dir = os.path.join("data", "reports", f"segmentation_{task_id}")
            os.makedirs(out_dir, exist_ok=True)
            result = segment_and_export_full(dicom_folder, out_dir, threshold=(threshold_min, threshold_max))
            _tasks[task_id] = {"status": "done", "result": result}
        except EmptyMaskError as e:
            _tasks[task_id] = {"status": "error", "detail": str(e)}
        except Exception as e:
            _tasks[task_id] = {"status": "error", "detail": str(e)}

    background_tasks.add_task(_run)
    return {"task_id": task_id, "status": "pending"}

@app.get("/task_status/{task_id}")
async def task_status(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]

@app.post("/upload_dicom/")
async def upload_dicom(
    files: List[UploadFile] = File(...),
    threshold_min: int = Form(30),
    threshold_max: int = Form(300),
):
    """Принимает один или несколько DICOM-файлов, сохраняет во временную папку и запускает сегментацию."""
    import uuid
    # Сохраняем файлы через общий сервис
    temp_root = dicom_service.save_uploaded_files([(f.filename, f.file.read()) for f in files])
    # Запустим полную сегментацию
    try:
        out_dir = os.path.join("data", "reports", f"segmentation_{uuid.uuid4().hex[:8]}")
        os.makedirs(out_dir, exist_ok=True)
        result = segment_and_export_full(temp_root, out_dir, threshold=(threshold_min, threshold_max))
        return JSONResponse({
            "nifti_mask_path": result["nifti"],
            "stl_path": result["stl"],
            "gltf_path": result["gltf"],
            "mask_png_dir": result["mask_png_dir"],
            "message": "Импорт и сегментация выполнены успешно"
        })
    except EmptyMaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Глоба��ьный обработчик ошибок: сохраняет ошибку в фай�� и возвращае�� JSON с ошибкой
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
