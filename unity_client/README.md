# Unity Client (AR Laparoscope)

This folder contains the Unity 2022.3 LTS project that visualises segmentation results produced by the backend.

## Quick start
1. Install **Unity Hub** + **Unity 2022.3 LTS** with Android/iOS + Windows build support.
2. In Unity Hub click **Open** and choose this `unity_client` directory.
3. When packages resolve, open the scene at `Assets/Scenes/ModelViewer.unity`.
4. Enter Play-mode or build to device. Press **Load** and enter STL/GLB URL (e.g. `http://localhost:8000/static/reports/segmentation_xxxx/mask.glb`).

## Key packages
* **glTFast** `v6.2.0` – runtime glTF/GLB loader (via UPM).
* **AR Foundation** `6.0` – optional; not required for desktop viewer.

## Structure
```
unity_client/
  Packages/manifest.json   ← UPM dependencies
  Assets/
    Scenes/ModelViewer.unity   ← main scene (text-based YAML)
    Scripts/ModelViewer/ModelLoader.cs  ← runtime loader script
```

## Backend integration
Backend produces GLB at `/upload_dicom/` response (`gltf_path`). Copy the URL or host file via local server and paste into UI field in the viewer.
