using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

/// <summary>
/// Simple UI wizard for pulling DICOM series from Orthanc PACS via backend endpoint.
/// Requires backend /import_and_validate_pacs/ that returns list of valid files.
/// </summary>
public class PacsPullWizard : MonoBehaviour
{
    public InputField orthancUrlField;
    public InputField seriesUidField;
    public InputField usernameField;
    public InputField passwordField;
    public Button fetchButton;
    public Text statusText;

    private const string BackendEndpoint = "http://localhost:8000/import_and_validate_pacs/";

    private void Awake()
    {
        fetchButton.onClick.AddListener(OnFetchClicked);
    }

    private void OnFetchClicked()
    {
        StartCoroutine(FetchRoutine());
    }

    private IEnumerator FetchRoutine()
    {
        statusText.text = "Fetching…";
        WWWForm form = new WWWForm();
        form.AddField("orthanc_url", orthancUrlField.text);
        form.AddField("series_uid", seriesUidField.text);
        if (!string.IsNullOrEmpty(usernameField.text)) form.AddField("username", usernameField.text);
        if (!string.IsNullOrEmpty(passwordField.text)) form.AddField("password", passwordField.text);

        using UnityWebRequest req = UnityWebRequest.Post(BackendEndpoint, form);
        yield return req.SendWebRequest();
        if (req.result == UnityWebRequest.Result.Success)
        {
            statusText.text = "PACS import success!";
            Debug.Log(req.downloadHandler.text);
        }
        else
        {
            statusText.text = "Error: " + req.error;
            Debug.LogError(req.error);
        }
    }
}
