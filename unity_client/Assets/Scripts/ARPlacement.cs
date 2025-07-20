using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace LaprascopeAR
{
    /// <summary>
    /// Places the first loaded GLTF model onto a detected horizontal plane on tap.
    /// Attach to ARSessionOrigin.
    /// </summary>
    [RequireComponent(typeof(ARRaycastManager))]
    public class ARPlacement : MonoBehaviour
    {
        [SerializeField] private Camera arCamera;
        private ARRaycastManager _raycastManager;
        private static readonly List<ARRaycastHit> Hits = new();
        private GameObject _loadedModel;
        private bool _placed;

        private void Awake()
        {
            _raycastManager = GetComponent<ARRaycastManager>();
        }

        private void Update()
        {
            if (_placed) return;
            if (Input.touchCount == 0) return;
            var touch = Input.GetTouch(0);
            if (touch.phase != TouchPhase.Ended) return;
            if (_raycastManager.Raycast(touch.position, Hits, TrackableType.PlaneWithinPolygon))
            {
                var hitPose = Hits[0].pose;
                _loadedModel = GameObject.Find("GLTFModel");
                if (_loadedModel == null) return;
                _loadedModel.transform.position = hitPose.position;
                _loadedModel.transform.rotation = hitPose.rotation;
                _placed = true;
            }
        }
    }
}
