"""Anonymize DICOM series in a directory tree.

Usage (PowerShell):
    python anonymize_dicom.py -i C:\data\raw_dicom -o C:\data\anon_dicom

The script copies the directory tree from input to output, removing
patient-identifying tags as defined in DICOM PS3.15.  UIDs are re-generated,
InstanceNumber and ImagePositionPatient are preserved.
"""

import argparse
import shutil
from pathlib import Path
from typing import List

import pydicom
from pydicom.uid import generate_uid

# Tags to delete completely (PHI)
PHI_TAGS: List[str] = [
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "PatientAge",
    "PatientAddress",
    "PatientWeight",
    "AccessionNumber",
    "InstitutionName",
]

# Tags whose UID should be replaced with a random UID
auto_uid_tags = [
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
]

def anonymize_file(src: Path, dst: Path) -> None:
    ds = pydicom.dcmread(src, force=True)
    # Remove PHI tags
    for tag in PHI_TAGS:
        if tag in ds:
            del ds[tag]
    # Replace UIDs
    for tag in auto_uid_tags:
        if tag in ds:
            ds[tag].value = generate_uid()
    # Set dummy patient name to keep software happy
    ds.PatientName = "ANONYMIZED"
    ds.save_as(dst)


def anonymize_series(input_dir: Path, output_dir: Path) -> None:
    """Recursively copy and anonymize all DICOM files."""
    for file_path in input_dir.rglob("*.dcm"):
        rel = file_path.relative_to(input_dir)
        dst_path = output_dir / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            anonymize_file(file_path, dst_path)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] Skip {file_path}: {exc}")


def parse_args():
    parser = argparse.ArgumentParser(description="Anonymize DICOM directory tree.")
    parser.add_argument("-i", "--input", required=True, type=Path, help="Input directory with DICOM")
    parser.add_argument("-o", "--output", required=True, type=Path, help="Output directory for anonymized DICOM")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    anonymize_series(args.input, args.output)
    print("Anonymization completed →", args.output)


if __name__ == "__main__":
    main()
