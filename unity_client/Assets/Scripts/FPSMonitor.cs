using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Simple FPS monitor that computes moving average FPS and displays it on screen.
/// </summary>
public class FPSMonitor : MonoBehaviour {
    public float updateInterval = 0.5f;
    public Text fpsText;

    private int _frames;
    private float _accum;
    private float _timeLeft;
    public float AverageFPS { get; private set; }

    void Start() {
        if (!fpsText) {
            var canvas = FindObjectOfType<Canvas>();
            if (!canvas) {
                canvas = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster)).GetComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            }
            var txtGo = new GameObject("FPSText", typeof(Text));
            txtGo.transform.SetParent(canvas.transform, false);
            fpsText = txtGo.GetComponent<Text>();
            fpsText.alignment = TextAnchor.UpperLeft;
            fpsText.fontSize = 20;
            fpsText.color = Color.white;
            fpsText.rectTransform.anchoredPosition = new Vector2(10, -10);
        }
        _timeLeft = updateInterval;
    }

    void Update() {
        _timeLeft -= Time.deltaTime;
        _accum += Time.timeScale / Time.deltaTime;
        ++_frames;

        if (_timeLeft <= 0.0f) {
            AverageFPS = _accum / _frames;
            fpsText.text = $"FPS: {AverageFPS:F1}";
            fpsText.color = AverageFPS < 30 ? Color.red : (AverageFPS < 45 ? Color.yellow : Color.green);
            _timeLeft = updateInterval;
            _accum = 0;
            _frames = 0;
        }
    }
}
