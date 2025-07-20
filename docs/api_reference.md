# REST API Reference

OpenAPI auto-generated docs are available at **`/docs`** when the backend is running. This page complements that with explanations and typical request / response examples.

---

## Health
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |

### Response
```json
{
  "status": "ok"
}
```

---

## Upload DICOM & Segment (Sync)
| Method | Path |
|--------|------|
| `POST` | `/upload_dicom/` |

### Request (multipart/form-data)
```
files[]: slice1.dcm
files[]: slice2.dcm
...
```

### Response 200
```json
{
  "stl_path": "outputs/seg_20250720_120010.stl",
  "gltf_path": "outputs/seg_20250720_120010.glb",
  "meta": {
    "voxels": 123456,
    "threshold": 200
  }
}
```

### Errors
| Code | Reason |
|------|--------|
| 400 | EmptyMaskError — segmentation produced zero voxels |
| 422 | Validation (no files) |

---

## Segment DICOM (Async)
| Method | Path |
|--------|------|
| `POST` | `/segment_dicom_async` |

Returns task id:
```json
{"task_id": "c8f9c5b3"}
```

Poll:
```
GET /task_status/c8f9c5b3
```
Possible states:
| Status | Payload |
|---------|---------|
| `pending` | `{progress: 0}` |
| `running` | `{progress: 42}` |
| `done` | Same schema as sync endpoint |
| `error` | `{error: "EmptyMaskError"}` |

---

## Static Assets
Segmented GLTF/STL files are served by `StaticFiles` under `/outputs/*` (path returned in JSON).

Example:
```
GET http://localhost:8000/outputs/seg_20250720_120010.glb
```

---

## Authentication
None (prototype). For production add JWT via `fastapi-users`.

---

## Versioning
Base path `/v1` reserved but not yet activated.
