#if UNITY_STANDALONE || UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

/// <summary>
/// Allows user to drag-and-drop a folder containing DICOM files onto the application window (Standalone/Editor).
/// It zips the folder, uploads to backend /upload_dicom_zip/ endpoint, and displays status.
/// </summary>
public class DicomDragDropHandler : MonoBehaviour
{
    [Tooltip("Backend URL for DICOM upload (POST zip)")]
    public string backendUrl = "http://localhost:8000/upload_dicom_zip/";

    [Header("UI")]
    public Text statusText;

    private readonly List<string> _draggedPaths = new();

    private void OnGUI()
    {
        Event evt = Event.current;
        if (evt.type == EventType.DragUpdated || evt.type == EventType.DragPerform)
        {
            DragAndDrop.visualMode = DragAndDropVisualMode.Copy;
            if (evt.type == EventType.DragPerform)
            {
                DragAndDrop.AcceptDrag();
                _draggedPaths.Clear();
                foreach (string path in DragAndDrop.paths)
                {
                    if (Directory.Exists(path))
                        _draggedPaths.Add(path);
                }
                if (_draggedPaths.Count > 0)
                {
                    foreach (var p in _draggedPaths)
                        Debug.Log("Dropped folder: " + p);
                    StartCoroutine(UploadRoutine(_draggedPaths[0]));
                }
            }
            evt.Use();
        }
    }

    private IEnumerator<UnityWebRequestAsyncOperation> UploadRoutine(string folderPath)
    {
        statusText.text = "Zipping DICOM…";
        string zipPath = Path.Combine(Path.GetTempPath(), Path.GetFileName(folderPath) + ".zip");
        if (File.Exists(zipPath)) File.Delete(zipPath);
        System.IO.Compression.ZipFile.CreateFromDirectory(folderPath, zipPath);

        byte[] bytes = File.ReadAllBytes(zipPath);
        var form = new WWWForm();
        form.AddBinaryData("file", bytes, Path.GetFileName(zipPath), "application/zip");
        statusText.text = "Uploading…";
        using var request = UnityWebRequest.Post(backendUrl, form);
        yield return request.SendWebRequest();
        if (request.result == UnityWebRequest.Result.Success)
        {
            statusText.text = "Upload success!";
        }
        else
        {
            statusText.text = "Upload failed: " + request.error;
        }
        File.Delete(zipPath);
    }
}
#endif
