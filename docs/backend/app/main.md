# backend/app/main.py — FastAPI Application

## Path & Summary
`backend/app/main.py` is the single entry-point for the REST API. It wires routers, background tasks, and error handlers.

## Responsibilities
1. Instantiate `FastAPI` app.
2. Expose health, DICOM upload, segmentation (sync & async) endpoints.
3. Handle `EmptyMaskError` globally → return HTTP 400.
4. Prototype in-memory background task queue via `BackgroundTasks`.

## Key Functions / Classes
| Name | Purpose |
|------|---------|
| `create_app()` | Factory returning FastAPI instance (used by tests) |
| `/health` GET | Liveness check returns JSON `{status: 'ok'}` |
| `/upload_dicom/` POST | Accepts multiple DICOM files → saves to temp → segmentation → returns GLTF & STL paths |
| `/segment_dicom_async` POST | Same as above but queues background task and returns `task_id` |
| `/task_status/{task_id}` GET | Poll async task result or progress |

## Typical Flow
```mermaid
sequenceDiagram
Client→>API: POST /upload_dicom (files)
API->>dicom_service: save_uploaded_files
API->>segmentation: simple_threshold_segmentation → mask_to_gltf/stl
API-->>Client: 200 + download URLs
```

## Error Handling
* `EmptyMaskError` → HTTP 400 with message "Segmentation mask is empty".
* Unhandled exception → HTTP 500.

## Tests
* `test_health.py` verifies 200.
* `test_upload_dicom_e2e.py` covers full happy-path.
* `test_empty_mask.py` checks 400 on empty segmentation.

## Dependencies
```
fastapi, pydantic, uvicorn
simpleitk, pydicom, numpy, trimesh
```

Run locally:
```bash
uvicorn backend.app.main:app --reload
```
