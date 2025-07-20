using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using LaprascopeAR;
using GLTFast;

namespace Tests
{
    public class ModelLoaderTests
    {
        private const string SampleGlb = "sample.glb"; // Put small GLB into StreamingAssets

        [UnityTest]
        public IEnumerator LoadSampleGlbFromStreamingAssets()
        {
            string path = System.IO.Path.Combine(Application.streamingAssetsPath, SampleGlb);
            var loaderGO = new GameObject("Loader", typeof(ModelLoader));
            var loader = loaderGO.GetComponent<ModelLoader>();

            bool done = false;
            // Use GltfImport directly for headless test
            var gltf = new GltfImport();
            var task = gltf.Load(path);
            while (!task.IsCompleted) yield return null;
            Assert.IsTrue(task.Result, "glTF failed to load");
            done = task.Result;
            Assert.IsTrue(done);
        }
    }
}
