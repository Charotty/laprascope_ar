using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Simple runtime panel with sliders to fine-tune position (XYZ) and rotation (Yaw/Pitch/Roll)
/// of a target GameObject (e.g., kidney parent). Saves/loads transform as JSON in StreamingAssets.
/// </summary>
public class TransformCalibrationUI : MonoBehaviour
{
    [Tooltip("Object to calibrate (parent of model)")]
    public Transform targetTransform;

    [Header("UI Prefabs")]
    public GameObject sliderPrefab;
    public GameObject labelPrefab;

    private const string FILE_NAME = "transform.json";
    private readonly string _savePath = System.IO.Path.Combine(Application.streamingAssetsPath, FILE_NAME);

    private Slider _x, _y, _z, _yaw, _pitch, _roll;

    private void Start()
    {
        if (!targetTransform) targetTransform = transform;

        var grid = new GameObject("CalibrationPanel", typeof(RectTransform), typeof(GridLayoutGroup));
        var canvas = FindObjectOfType<Canvas>();
        if (!canvas)
        {
            canvas = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster)).GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        }
        grid.transform.SetParent(canvas.transform, false);
        var layout = grid.GetComponent<GridLayoutGroup>();
        layout.cellSize = new Vector2(200, 40);

        _x = CreateSlider(grid.transform, "X", targetTransform.localPosition.x, val => Apply());
        _y = CreateSlider(grid.transform, "Y", targetTransform.localPosition.y, val => Apply());
        _z = CreateSlider(grid.transform, "Z", targetTransform.localPosition.z, val => Apply());
        _yaw   = CreateSlider(grid.transform, "Yaw", targetTransform.localEulerAngles.y, val => Apply());
        _pitch = CreateSlider(grid.transform, "Pitch", targetTransform.localEulerAngles.x, val => Apply());
        _roll  = CreateSlider(grid.transform, "Roll", targetTransform.localEulerAngles.z, val => Apply());

        // Save / load buttons
        CreateButton(grid.transform, "Save", Save);
        CreateButton(grid.transform, "Load", Load);

        if (System.IO.File.Exists(_savePath)) Load();
    }

    private Slider CreateSlider(Transform parent, string name, float defaultValue, UnityEngine.Events.UnityAction<float> onChanged)
    {
        var go = Instantiate(sliderPrefab, parent);
        go.name = name + "Slider";
        var label = Instantiate(labelPrefab, parent);
        label.GetComponent<Text>().text = name;

        var slider = go.GetComponent<Slider>();
        slider.minValue = -100; slider.maxValue = 100;
        slider.value = defaultValue;
        slider.onValueChanged.AddListener(onChanged);
        return slider;
    }

    private void CreateButton(Transform parent, string txt, UnityEngine.Events.UnityAction action)
    {
        var btnObj = new GameObject(txt + "Button", typeof(RectTransform), typeof(Button), typeof(Image));
        btnObj.transform.SetParent(parent, false);
        var txtGo = new GameObject("Text", typeof(Text));
        txtGo.transform.SetParent(btnObj.transform, false);
        var t = txtGo.GetComponent<Text>();
        t.text = txt; t.alignment = TextAnchor.MiddleCenter; t.color = Color.black;
        var btn = btnObj.GetComponent<Button>();
        btn.onClick.AddListener(action);
        var rt = btnObj.GetComponent<RectTransform>();
        rt.sizeDelta = new Vector2(200, 40);
    }

    private void Apply()
    {
        if (!targetTransform) return;
        targetTransform.localPosition = new Vector3(_x.value, _y.value, _z.value);
        targetTransform.localEulerAngles = new Vector3(_pitch.value, _yaw.value, _roll.value);
    }

    private void Save()
    {
        var data = new TransformData(targetTransform);
        System.IO.File.WriteAllText(_savePath, JsonUtility.ToJson(data, true));
        Debug.Log("Transform saved → " + _savePath);
    }

    private void Load()
    {
        if (!System.IO.File.Exists(_savePath)) return;
        var json = System.IO.File.ReadAllText(_savePath);
        var data = JsonUtility.FromJson<TransformData>(json);
        data.ApplyTo(targetTransform);
        // Update sliders
        _x.value = targetTransform.localPosition.x;
        _y.value = targetTransform.localPosition.y;
        _z.value = targetTransform.localPosition.z;
        _yaw.value = targetTransform.localEulerAngles.y;
        _pitch.value = targetTransform.localEulerAngles.x;
        _roll.value = targetTransform.localEulerAngles.z;
    }

    [System.Serializable]
    private class TransformData
    {
        public Vector3 position;
        public Vector3 rotation;
        public TransformData(Transform t)
        {
            position = t.localPosition;
            rotation = t.localEulerAngles;
        }
        public void ApplyTo(Transform t)
        {
            t.localPosition = position;
            t.localEulerAngles = rotation;
        }
    }
}
