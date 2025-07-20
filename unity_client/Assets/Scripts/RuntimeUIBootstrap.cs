using UnityEngine;
using UnityEngine.UI;

namespace LaprascopeAR
{
    /// <summary>
    /// Creates a minimal Canvas with InputField + Button at runtime if none present.
    /// This avoids manual UI setup in prototype stage.
    /// </summary>
    [RequireComponent(typeof(ModelLoader))]
    public class RuntimeUIBootstrap : MonoBehaviour
    {
        private ModelLoader _loader;

        private void Awake()
        {
            _loader = GetComponent<ModelLoader>();
            if (_loader == null)
                return;

            if (_loader.urlInput == null || _loader.loadButton == null)
            {
                BuildUI();
            }
        }

        private void BuildUI()
        {
            var canvasGO = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGO.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;

            var inputGO = new GameObject("URLInput", typeof(Image), typeof(InputField));
            inputGO.transform.SetParent(canvasGO.transform, false);
            var inputRect = inputGO.GetComponent<RectTransform>();
            inputRect.anchorMin = new Vector2(0.5f, 1);
            inputRect.anchorMax = new Vector2(0.5f, 1);
            inputRect.pivot = new Vector2(0.5f, 1);
            inputRect.anchoredPosition = new Vector2(0, -40);
            inputRect.sizeDelta = new Vector2(300, 30);
            var inputField = inputGO.GetComponent<InputField>();

            var buttonGO = new GameObject("LoadButton", typeof(Image), typeof(Button));
            buttonGO.transform.SetParent(canvasGO.transform, false);
            var btnRect = buttonGO.GetComponent<RectTransform>();
            btnRect.anchorMin = new Vector2(0.5f, 1);
            btnRect.anchorMax = new Vector2(0.5f, 1);
            btnRect.pivot = new Vector2(0.5f, 1);
            btnRect.anchoredPosition = new Vector2(0, -80);
            btnRect.sizeDelta = new Vector2(100, 30);
            var button = buttonGO.GetComponent<Button>();

            // Add text to button
            var txtGO = new GameObject("Text", typeof(Text));
            txtGO.transform.SetParent(buttonGO.transform, false);
            var txt = txtGO.GetComponent<Text>();
            txt.text = "Load";
            txt.alignment = TextAnchor.MiddleCenter;
            txt.rectTransform.anchorMin = Vector2.zero;
            txt.rectTransform.anchorMax = Vector2.one;
            txt.rectTransform.offsetMin = Vector2.zero;
            txt.rectTransform.offsetMax = Vector2.zero;

            // Toast label
            var toastGO = new GameObject("Toast", typeof(Text));
            toastGO.transform.SetParent(canvasGO.transform, false);
            var toast = toastGO.GetComponent<Text>();
            toast.alignment = TextAnchor.MiddleCenter;
            toast.color = Color.red;
            toast.fontSize = 18;
            var toastRect = toast.GetComponent<RectTransform>();
            toastRect.anchorMin = new Vector2(0.5f, 1);
            toastRect.anchorMax = new Vector2(0.5f, 1);
            toastRect.pivot = new Vector2(0.5f, 1);
            toastRect.anchoredPosition = new Vector2(0, -120);

            // Wire to ModelLoader
            _loader.urlInput = inputField;
            _loader.loadButton = button;
            button.onClick.AddListener(() => _loader.SendMessage("OnLoadClicked", SendMessageOptions.DontRequireReceiver));

            // Pick File button (editor/standalone only)
#if !UNITY_WEBGL && !UNITY_IOS && !UNITY_ANDROID
            var pickGO = new GameObject("PickButton", typeof(Image), typeof(Button));
            pickGO.transform.SetParent(canvasGO.transform, false);
            var pickRect = pickGO.GetComponent<RectTransform>();
            pickRect.anchorMin = new Vector2(0.5f, 1);
            pickRect.anchorMax = new Vector2(0.5f, 1);
            pickRect.pivot = new Vector2(0.5f, 1);
            pickRect.anchoredPosition = new Vector2(120, -80);
            pickRect.sizeDelta = new Vector2(120, 30);
            var pickBtn = pickGO.GetComponent<Button>();
            var pickTxtGO = new GameObject("Text", typeof(Text));
            pickTxtGO.transform.SetParent(pickGO.transform, false);
            var pickTxt = pickTxtGO.GetComponent<Text>();
            pickTxt.text = "Pick File";
            pickTxt.alignment = TextAnchor.MiddleCenter;
            pickTxt.rectTransform.anchorMin = Vector2.zero;
            pickTxt.rectTransform.anchorMax = Vector2.one;
            pickTxt.rectTransform.offsetMin = Vector2.zero;
            pickTxt.rectTransform.offsetMax = Vector2.zero;
            pickBtn.onClick.AddListener(() => _loader.SendMessage("OnPickFileClicked", SendMessageOptions.DontRequireReceiver));
#endif

            // Reset view button
            var resetGO = new GameObject("ResetButton", typeof(Image), typeof(Button));
            resetGO.transform.SetParent(canvasGO.transform, false);
            var resetRect = resetGO.GetComponent<RectTransform>();
            resetRect.anchorMin = new Vector2(0.5f, 1);
            resetRect.anchorMax = new Vector2(0.5f, 1);
            resetRect.pivot = new Vector2(0.5f, 1);
            resetRect.anchoredPosition = new Vector2(-120, -80);
            resetRect.sizeDelta = new Vector2(120, 30);
            var resetBtn = resetGO.GetComponent<Button>();
            var resetTxtGO = new GameObject("Text", typeof(Text));
            resetTxtGO.transform.SetParent(resetGO.transform, false);
            var resetTxt = resetTxtGO.GetComponent<Text>();
            resetTxt.text = "Reset View";
            resetTxt.alignment = TextAnchor.MiddleCenter;
            resetTxt.rectTransform.anchorMin = Vector2.zero;
            resetTxt.rectTransform.anchorMax = Vector2.one;
            resetTxt.rectTransform.offsetMin = Vector2.zero;
            resetTxt.rectTransform.offsetMax = Vector2.zero;

            var cam = Camera.main?.GetComponent<LaprascopeAR.OrbitCamera>();
            if (cam != null)
            {
                resetBtn.onClick.AddListener(cam.ResetView);
            }

            // Register toast
            ToastUI.Toast.Register(toast);
        }
    }
}
