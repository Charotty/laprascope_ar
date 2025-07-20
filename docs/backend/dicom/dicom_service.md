# backend/dicom/dicom_service.py — DICOM Utilities

## Path & Summary
Handles **upload, organisation and conversion** of DICOM series.

## Responsibilities
1. Persist user-uploaded slices to temp dir.
2. Detect valid DICOM files (via pydicom) and discard garbage.
3. Group slices into series (by StudyUID / SeriesUID).
4. Convert series → 3-D numpy volume via SimpleITK.
5. Provide helper `collect_series()` for tests and CLI.

## Key API
| Function | Signature | Notes |
|----------|-----------|-------|
| `save_uploaded_files(upload_files) -> Path` | Saves FastAPI `UploadFile` list to `tempfile.mkdtemp()` |
| `collect_series(folder) -> List[File]` | Recursively find DICOM files, grouped by series |
| `series_to_numpy(folder) -> np.ndarray` | Reads with `sitk.ReadImage`, returns `np.asarray(img)` |
| `_is_dicom(path) -> bool` | Quick magic-byte check then pydicom.dcmread(head_only) |

## Typical Usage
```python
folder = dicom_service.save_uploaded_files(files)
volume = dicom_service.series_to_numpy(folder)
```

## Error Handling
* Raises `ValueError` if no valid DICOM found.
* Logs warnings for unreadable slices.

## Tests
* `test_upload_dicom_e2e.py` covers full pipeline.

## Dependencies
```
pydicom, SimpleITK, numpy, pathlib, tempfile
```
