# backend/segmentation/segmentation.py — Threshold Segmentation Pipeline

## Path & Summary
Performs **very simple MVP segmentation** by thresholding HU values on CT volume and exporting meshes.

## Responsibilities
1. `simple_threshold_segmentation(vol, threshold)` → binary mask.
2. `_ensure_non_empty(mask)` → raises `EmptyMaskError` if mask sum == 0.
3. `mask_to_stl(mask, voxel_spacing, out_path)` → marching cubes → `trimesh` export.
4. `mask_to_gltf(mask, voxel_spacing, out_path)` → same but glTF binary.
5. Custom `EmptyMaskError` (imported by FastAPI for 400).

## Algorithm Details
```
mask = vol >= threshold  # numpy
verts, faces, _ = skimage.measure.marching_cubes(mask, 0)
mesh = trimesh.Trimesh(verts * spacing, faces)
```

*This is intentionally naive and will be replaced by ML segmentation later.*

## Typical Usage
```python
mask = simple_threshold_segmentation(vol, 200)
mask_to_stl(mask, spacing, "output.stl")
```

## Error Handling
* Empty masks raise `EmptyMaskError`.
* File I/O errors are propagated.

## Tests
* `test_segmentation.py` checks mask correctness.
* `test_empty_mask.py` asserts exception.

## Dependencies
```
numpy, skimage, trimesh
```
