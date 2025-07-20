using System;
using System.Threading.Tasks;
using GLTFast;
using UnityEngine;
using UnityEngine.UI;
using ToastUI;

namespace LaprascopeAR
{
    /// <summary>
    /// Runtime loader of a GLB/GLTF model via URL specified in UI.
    /// Attach this script to any GameObject in the scene and assign
    /// references via Inspector.
    /// </summary>
    public class ModelLoader : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] private InputField urlInput;
        [SerializeField] private Button loadButton;
        [Tooltip("Parent transform where instantiated model will be placed (optional)")]
        [SerializeField] private Transform modelParent;

        private GameObject _loadedGO;

        private void Awake()
        {
            if (loadButton != null)
            {
                loadButton.onClick.AddListener(OnLoadClicked);
            }
        }

        private async void OnLoadClicked()
        {
            string url = urlInput != null ? urlInput.text : string.Empty;
            if (string.IsNullOrWhiteSpace(url))
            {
                ToastUI.Toast.Show("URL field is empty");
                return;
            }

            await LoadModel(url);
        }

        /// <summary>
        /// Downloads glTF/GLB from <paramref name="url"/> and instantiates main scene.
        /// If a model was previously loaded, it will be destroyed first.
        /// </summary>
        private async Task LoadModel(string url)
        {
            try
            {
                if (_loadedGO != null)
                {
                    Destroy(_loadedGO);
                    _loadedGO = null;
                }

                var gltf = new GltfImport();
                bool success = await gltf.Load(new Uri(url));
                if (!success)
                {
                    ToastUI.Toast.Show($"Failed to load GLTF from {url}");
                    return;
                }

                // Create root object for model
                _loadedGO = new GameObject("GLTFModel");
                if (modelParent != null)
                {
                    _loadedGO.transform.SetParent(modelParent, false);
                }

                // Instantiate into scene
                success = await gltf.InstantiateMainSceneAsync(_loadedGO.transform);
                if (!success)
                {
                    ToastUI.Toast.Show("Failed to instantiate GLTF scene");
                    Destroy(_loadedGO);
                }
            }
            catch (Exception ex)
            {
                ToastUI.Toast.Show(ex.Message);
            }
        }

#if UNITY_EDITOR || UNITY_STANDALONE
        // Called by RuntimeUIBootstrap
        private void OnPickFileClicked()
        {
#if UNITY_EDITOR
            string path = UnityEditor.EditorUtility.OpenFilePanel("Select GLB/GLTF model", "", "glb,gltf");
            if (!string.IsNullOrEmpty(path))
            {
                urlInput.text = path;
                OnLoadClicked();
            }
#else
            // Standalone: simple Windows dialog (requires System.Windows.Forms, not available by default)
            ToastUI.Toast.Show("File picker not implemented for standalone build");
#endif
        }
#endif
    }
}
