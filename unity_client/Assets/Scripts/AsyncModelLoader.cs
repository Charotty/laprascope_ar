using System.Collections;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

/// <summary>
/// Loads a GLTF/GLB model from an Addressable Asset asynchronously.
/// </summary>
public class AsyncModelLoader : MonoBehaviour
{
    [Tooltip("Addressables key of the model asset (GLB prefab)")]
    public string addressKey;

    [Tooltip("Parent transform where model instance will spawn")]
    public Transform parent;

    private GameObject _instance;

    public void Load() => StartCoroutine(LoadRoutine());

    private IEnumerator LoadRoutine()
    {
        if (_instance) Destroy(_instance);
        var handle = Addressables.InstantiateAsync(addressKey, parent);
        yield return handle;
        if (handle.Status == AsyncOperationStatus.Succeeded)
        {
            _instance = handle.Result;
            Debug.Log($"Model {addressKey} loaded async");
        }
        else
        {
            Debug.LogError("Addressables load failed: " + handle.OperationException);
        }
    }

    private void OnDestroy()
    {
        if (_instance)
            Addressables.ReleaseInstance(_instance);
    }
}
