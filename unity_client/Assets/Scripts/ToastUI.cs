using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace ToastUI
{
    /// <summary>
    /// Very lightweight toast utility for prototype. Shows red text at top of screen for a few seconds.
    /// Call <see cref="Register"/> once with a Text reference (RuntimeUIBootstrap does this automatically).
    /// Then call <see cref="Show"/> from anywhere.
    /// </summary>
    public static class Toast
    {
        private static Text _toast;
        private static MonoBehaviour _runner;

        public static void Register(Text toastText)
        {
            _toast = toastText;
            _toast.gameObject.SetActive(false);
            // create runner object if not exists
            if (_runner == null)
            {
                var go = new GameObject("ToastRunner");
                Object.DontDestroyOnLoad(go);
                _runner = go.AddComponent<ToastRunner>();
            }
        }

        public static void Show(string message, float duration = 2f)
        {
            if (_toast == null)
            {
                Debug.LogWarning("ToastUI not registered");
                return;
            }
            _toast.text = message;
            _toast.gameObject.SetActive(true);
            _runner.StopAllCoroutines();
            _runner.StartCoroutine(HideAfter(duration));
        }

        private static IEnumerator HideAfter(float seconds)
        {
            yield return new WaitForSeconds(seconds);
            if (_toast != null)
            {
                _toast.gameObject.SetActive(false);
            }
        }

        private class ToastRunner : MonoBehaviour { }
    }
}
