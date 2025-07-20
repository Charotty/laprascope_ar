# Backend Documentation

This section documents **every Python module** in `backend/` used by Laprascope AR.

| Module | Description |
|--------|-------------|
| `app/` | FastAPI application entry-point (`main.py`) and router definitions |
| `dicom/` | Utilities for DICOM handling and conversion (`dicom_service.py`, etc.) |
| `segmentation/` | Basic threshold segmentation pipeline and 3-D export helpers |
| `calculations/` | Algorithms for trocar point generation on meshes |
| `export/` | STL / GLTF writing helpers (future) |
| `models/` | Pydantic models & schemas (minimal) |
| `tests/` | Pytest suite: unit, integration, e2e |

Each sub-page gives full technical commentary:

* [FastAPI `main.py`](app/main.md)
* [DICOM Service](dicom/dicom_service.md)
* [Segmentation Pipeline](segmentation/segmentation.md)
* [Trocar Calculations](calculations/trocar_calculations.md)
* [Tests Structure](tests.md)

---

## Environment & Dependencies

```
Python 3.10+
FastAPI, pydantic, uvicorn
SimpleITK, pydicom
numpy, trimesh
```

Install via:

```bash
pip install -r backend/requirements.txt
```

Run locally:

```bash
uvicorn backend.app.main:app --reload
```
