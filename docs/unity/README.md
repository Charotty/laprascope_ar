# Unity Client Documentation

This section describes the **runtime model viewer & AR client** residing in `unity_client/`.

## Project Info
* Unity Version: **2022.3 LTS**
* Packages:
  * `com.atteneder.gltfast` — Efficient glTF runtime loader.
  * `com.unity.xr.arfoundation` — AR plane detection & camera.
* Scenes: `Assets/Scenes/ModelViewer.unity` (single).

## Runtime Flow
1. **RuntimeUIBootstrap** generates minimal UI if missing.
2. User inputs URL or picks file → **ModelLoader** downloads / loads glTF.
3. Model instantiated under `GLTFModel` parent.
4. **OrbitCamera** enables orbit/zoom; pinch on mobile.
5. **ARPlacement** (if AR Session present) allows tap-to-place on plane.
6. Toast messages show errors.

## Building
```bash
# Open Unity Hub → add project unity_client
# Or CLI
unity -quit -batchmode -projectPath unity_client -executeMethod BuildScript.BuildWebGL
```

## Testing
* PlayMode tests in `Assets/Editor/ModelLoaderTests.cs`.
* CI pipeline runs Unity Test Runner (see `docs/ci_cd.md`).
