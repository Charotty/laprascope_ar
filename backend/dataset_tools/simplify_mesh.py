"""Simplify a mesh (STL/OBJ/GLB/GLTF) using trimesh + pyglet.

Usage:
    python simplify_mesh.py -i kidney.glb -o kidney_simpl.glb --ratio 0.3

Requires:
    pip install trimesh[all]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import trimesh

SUPPORTED_EXT = {".stl", ".obj", ".ply", ".glb", ".gltf"}

def simplify(mesh: trimesh.Trimesh, ratio: float) -> trimesh.Trimesh:
    target = int(mesh.faces.shape[0] * ratio)
    try:
        simplified = mesh.simplify_quadratic_decimation(target)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Decimation failed: {exc}") from exc
    return simplified


def parse_args():
    p = argparse.ArgumentParser(description="Simplify mesh with quadratic decimation")
    p.add_argument("-i", "--input", required=True, type=Path, help="Input mesh file")
    p.add_argument("-o", "--output", required=True, type=Path, help="Output mesh file")
    p.add_argument("-r", "--ratio", type=float, default=0.3, help="Fraction of faces to keep (0-1)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.input.suffix.lower() not in SUPPORTED_EXT:
        raise ValueError("Unsupported extension")
    mesh = trimesh.load(args.input, force='mesh')
    simplified = simplify(mesh, args.ratio)
    simplified.export(args.output)
    print(f"Saved simplified mesh → {args.output} (faces: {simplified.faces.shape[0]})")


if __name__ == "__main__":
    main()
