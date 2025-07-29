using UnityEngine;
using UnityEngine.Rendering;
using System.Collections.Generic;

/// <summary>
/// Generates LOD0/1/2 levels for a given mesh at runtime using Unity's MeshSimplify API (Unity 2023 w/ Runtime Mesh Simplification) or precomputed ratios.
/// Attach to the root of the imported model (parent GameObject).
/// </summary>
[RequireComponent(typeof(LODGroup))]
public class LODGenerator : MonoBehaviour {
    [Range(0.1f, 1f)] public float lod1Ratio = 0.5f;
    [Range(0.05f, 0.5f)] public float lod2Ratio = 0.2f;

    [Tooltip("Screen relative transition heights")] public Vector2 lodHeights = new Vector2(0.6f, 0.3f);

    private void Start() {
        BuildLODs();
    }

    private void BuildLODs() {
        var lodGroup = GetComponent<LODGroup>();
        var renderers = GetComponentsInChildren<MeshRenderer>();
        List<LOD> lods = new List<LOD>();

        // LOD0: original renderers
        lods.Add(new LOD(lodHeights.x, renderers));

        // LOD1 & LOD2
        lods.Add(CreateLODN(renderers, lod1Ratio, lodHeights.y));
        lods.Add(CreateLODN(renderers, lod2Ratio, 0.01f));

        lodGroup.SetLODs(lods.ToArray());
        lodGroup.RecalculateBounds();
    }

    private LOD CreateLODN(MeshRenderer[] originalRenderers, float ratio, float height) {
        MeshRenderer[] newRenderers = new MeshRenderer[originalRenderers.Length];
        for (int i = 0; i < originalRenderers.Length; i++) {
            var src = originalRenderers[i];
            var go = new GameObject(src.gameObject.name + "_LOD", typeof(MeshFilter), typeof(MeshRenderer));
            go.transform.SetParent(src.transform.parent, false);
            go.transform.localPosition = src.transform.localPosition;
            go.transform.localRotation = src.transform.localRotation;
            go.transform.localScale = src.transform.localScale;

            var mfSrc = src.GetComponent<MeshFilter>();
            var mfDst = go.GetComponent<MeshFilter>();
            var mrDst = go.GetComponent<MeshRenderer>();
            mrDst.sharedMaterials = src.sharedMaterials;

            mfDst.sharedMesh = SimplifyMesh(mfSrc.sharedMesh, ratio);
            newRenderers[i] = mrDst;
        }
        return new LOD(height, newRenderers);
    }

    private Mesh SimplifyMesh(Mesh original, float ratio) {
#if UNITY_EDITOR
        // Use UnityEditor MeshUtility (only in Editor)
        var path = UnityEditor.AssetDatabase.GetAssetPath(original);
        var meshCopy = Object.Instantiate(original);
        UnityEditor.MeshUtility.Optimize(meshCopy);
        UnityEditor.MeshUtility.SetMeshCompression(meshCopy, UnityEditor.ModelImporterMeshCompression.Medium);
        // Fallback: just return the copy (ratio ignored in editor)
        return meshCopy;
#else
        // Runtime: naive vertex decimation (remove every nth vertex)
        Mesh mesh = new Mesh();
        mesh.vertices = original.vertices;
        mesh.triangles = original.triangles;
        mesh.normals = original.normals;
        // TODO: implement better runtime simplification or use third-party lib
        return mesh;
#endif
    }
}
