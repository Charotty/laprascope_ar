"""Unit tests for anonymize_dicom.py.

These tests validate that PHI tags are stripped and UIDs are regenerated.
"""

from pathlib import Path

import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian

from backend.dataset_tools.anonymize_dicom import anonymize_file, PHI_TAGS


def _make_dummy_dicom(tmp_dir: Path) -> Path:
    """Create a dummy DICOM file containing PHI for testing."""
    file_path = tmp_dir / "test.dcm"
    meta = Dataset()
    meta.MediaStorageSOPClassUID = "1.2.3"
    meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = FileDataset(str(file_path), {}, file_meta=meta, preamble=b"\0" * 128)

    # PHI tags
    ds.PatientName = "John^Doe"
    ds.PatientID = "12345"
    ds.PatientBirthDate = "19600101"
    ds.StudyInstanceUID = "1.2.3.4.5"
    ds.SeriesInstanceUID = "1.2.3.4.5.6"
    ds.SOPInstanceUID = "1.2.3.4.5.6.7"

    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.save_as(file_path)
    return file_path


def test_anonymize_file(tmp_path: Path) -> None:
    src = _make_dummy_dicom(tmp_path)
    dst = tmp_path / "anon.dcm"

    anonymize_file(src, dst)
    ds = pydicom.dcmread(dst, force=True)

    # PHI tags must be absent
    for tag in PHI_TAGS:
        assert tag not in ds, f"{tag} was not removed"

    # UIDs must differ from original
    assert ds.StudyInstanceUID != "1.2.3.4.5"
    assert ds.SeriesInstanceUID != "1.2.3.4.5.6"
    assert ds.SOPInstanceUID != "1.2.3.4.5.6.7"

    # PatientName replaced
    assert ds.PatientName == "ANONYMIZED"
