# backend/tests — Test Suite Structure

Pytest directory covering unit, integration and end-to-end scenarios.

| Test File | Scope | Description |
|-----------|-------|-------------|
| `test_health.py` | Unit | FastAPI `/health` returns 200 & JSON |
| `test_segmentation.py` | Unit | `simple_threshold_segmentation` mask logic |
| `test_empty_mask.py` | Unit | `mask_to_stl` raises `EmptyMaskError` on zero mask |
| `test_trocar_calculations.py` | Unit | Trocar algorithm constraints |
| `test_upload_dicom_e2e.py` | E2E | Upload sample DICOM → GLTF/STL produced |

## Fixtures & Conventions
* **`client`** – FastAPI `TestClient` fixture (see `conftest.py`, future).
* Tests reside next to code for simplicity, but can be moved to root `tests/`.
* Naming: `test_*.py` for pytest discovery.

## Running Locally
```bash
pytest backend/tests -v
```

## CI Integration
* GitHub Action `python-ci.yml` installs deps, runs `pytest`, uploads coverage (future).
