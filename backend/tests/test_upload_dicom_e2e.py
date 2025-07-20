"""E2E test: upload small DICOM sample and ensure segmentation pipeline returns STL"""

import os
from pathlib import Path

import pydicom
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

# Use two slices from pydicom's public test data (small, <300 kB)
SAMPLE_FILES = [
    pydicom.data.get_testdata_file("CT_small.dcm"),
    pydicom.data.get_testdata_file("CT_small.dcm"),  # reuse same file, pipeline just needs >1 slice
]


def test_upload_dicom_e2e(tmp_path):
    files = [("files", (Path(fp).name, open(fp, "rb"), "application/dicom")) for fp in SAMPLE_FILES]
    response = client.post("/upload_dicom/", files=files)
    assert response.status_code == 200, response.text
    data = response.json()
    # Ensure STL path returned and file exists
    stl_path = data["stl_path"]
    assert stl_path.endswith(".stl")
    assert os.path.exists(stl_path)
