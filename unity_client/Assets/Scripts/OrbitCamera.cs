using UnityEngine;

namespace LaprascopeAR
{
    /// <summary>
    /// Very simple orbital camera around target at runtime with mouse / touch.
    /// Attach to main Camera. If target is null, will orbit around world origin.
    /// </summary>
    public class OrbitCamera : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private float distance = 0.5f; // meters
        [SerializeField] private float xSpeed = 120f;
        [SerializeField] private float ySpeed = 120f;
        [SerializeField] private float yMinLimit = -20f;
        [SerializeField] private float yMaxLimit = 80f;
        [SerializeField] private float zoomSpeed = 2f;
        [SerializeField] private float minDistance = 0.1f;
        [SerializeField] private float maxDistance = 2.0f;

        private float _x = 0f;
        private float _y = 0f;
        private float _initDistance;
        private Vector3 _initTargetPos;

        private void Start()
        {
            var angles = transform.eulerAngles;
            _x = angles.y;
            _y = angles.x;
            if (target == null)
            {
                target = new GameObject("CameraTarget").transform;
                target.position = Vector3.zero;
            }
            _initDistance = distance;
            _initTargetPos = target.position;
        }

        private void LateUpdate()
        {
            // Mouse
            if (Input.GetMouseButton(0))
            {
                _x += Input.GetAxis("Mouse X") * xSpeed * 0.02f;
                _y -= Input.GetAxis("Mouse Y") * ySpeed * 0.02f;
                _y = ClampAngle(_y, yMinLimit, yMaxLimit);
            }

            distance -= Input.GetAxis("Mouse ScrollWheel") * zoomSpeed;

            // Touch
            if (Input.touchSupported && Input.touchCount > 0)
            {
                var t0 = Input.GetTouch(0);
                if (Input.touchCount == 1 && t0.phase == TouchPhase.Moved)
                {
                    _x += t0.deltaPosition.x * xSpeed * 0.002f;
                    _y -= t0.deltaPosition.y * ySpeed * 0.002f;
                    _y = ClampAngle(_y, yMinLimit, yMaxLimit);
                }
                else if (Input.touchCount == 2)
                {
                    var t1 = Input.GetTouch(1);
                    // pinch zoom
                    var prevMag = (t0.position - t0.deltaPosition - (t1.position - t1.deltaPosition)).magnitude;
                    var curMag = (t0.position - t1.position).magnitude;
                    var diff = prevMag - curMag;
                    distance += diff * zoomSpeed * 0.0005f;
                }
            }

            distance = Mathf.Clamp(distance, minDistance, maxDistance);

            Quaternion rotation = Quaternion.Euler(_y, _x, 0);
            Vector3 position = rotation * new Vector3(0.0f, 0.0f, -distance) + target.position;

            transform.rotation = rotation;
            transform.position = position;
        }

        private static float ClampAngle(float angle, float min, float max)
        {
            if (angle < -360f) angle += 360f;
            if (angle > 360f) angle -= 360f;
            return Mathf.Clamp(angle, min, max);
        }

        public void ResetView()
        {
            _x = 0f;
            _y = 0f;
            distance = _initDistance;
            if (target != null) target.position = _initTargetPos;
        }
    }
}
