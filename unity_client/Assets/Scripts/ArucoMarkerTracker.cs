using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

#if OPENCV
using OpenCVForUnity.CoreModule;
using OpenCVForUnity.ImgprocModule;
using OpenCVForUnity.ObjdetectModule;
#endif

/// <summary>
/// Detects ArUco/AprilTag markers in the AR camera feed and invokes an event
/// when a marker with a specified ID is found.
/// Requires: ARCameraManager on same GameObject and OpenCVForUnity (define OPENCV).
/// </summary>
[RequireComponent(typeof(ARCameraManager))]
public class ArucoMarkerTracker : MonoBehaviour
{
    [Tooltip("Target marker ID (e.g., 0)")]
    public int targetMarkerId = 0;

    [Tooltip("World-space prefab to spawn at marker pose")]
    public GameObject markerPrefab;

    public event Action<Pose> OnMarkerDetected;

    private ARCameraManager _cameraManager;

#if OPENCV
    private Dictionary dictionary;
    private DetectorParameters detectorParams;
#endif

    private void Awake()
    {
        _cameraManager = GetComponent<ARCameraManager>();
#if OPENCV
        dictionary = Objdetect.getPredefinedDictionary(Objdetect.DICT_6X6_250);
        detectorParams = DetectorParameters.create();
#endif
    }

    private void OnEnable()
    {
        _cameraManager.frameReceived += OnCameraFrame;
    }

    private void OnDisable()
    {
        _cameraManager.frameReceived -= OnCameraFrame;
    }

    private void OnCameraFrame(ARCameraFrameEventArgs args)
    {
#if !OPENCV
        return; // Plugin not present.
#else
        if (!_cameraManager.TryAcquireLatestCpuImage(out XRCpuImage cpuImage))
            return;

        using (cpuImage)
        {
            var conversionParams = new XRCpuImage.ConversionParams
            {
                inputRect = new RectInt(0, 0, cpuImage.width, cpuImage.height),
                outputDimensions = new Vector2Int(cpuImage.width, cpuImage.height),
                outputFormat = TextureFormat.RGBA32,
                transformation = XRCpuImage.Transformation.MirrorY
            };

            int size = cpuImage.GetConvertedDataSize(conversionParams);
            var buffer = new NativeArray<byte>(size, Allocator.Temp);
            cpuImage.Convert(conversionParams, buffer);

            Mat img = new Mat(cpuImage.height, cpuImage.width, CvType.CV_8UC4);
            img.put(0, 0, buffer.ToArray());
            buffer.Dispose();

            // ArUco detection
            List<Mat> corners = new List<Mat>();
            Mat ids = new Mat();
            Aruco.detectMarkers(img, dictionary, corners, ids, detectorParams);

            if (!ids.empty())
            {
                for (int i = 0; i < ids.total(); i++)
                {
                    int id = (int)ids.get(i, 0)[0];
                    if (id == targetMarkerId)
                    {
                        // Compute center
                        double[] c0 = corners[i].get(0, 0);
                        double[] c2 = corners[i].get(0, 2);
                        Vector2 center = new Vector2((float)((c0[0] + c2[0]) / 2), (float)((c0[1] + c2[1]) / 2));

                        // Raycast into AR scene to approximate pose
                        var ray = _cameraManager.GetComponent<Camera>().ScreenPointToRay(center);
                        if (Physics.Raycast(ray, out RaycastHit hit))
                        {
                            Pose pose = new Pose(hit.point, Quaternion.LookRotation(hit.normal));
                            OnMarkerDetected?.Invoke(pose);
                            if (markerPrefab && hit.collider)
                            {
                                Instantiate(markerPrefab, pose.position, pose.rotation);
                            }
                        }
                        break;
                    }
                }
            }
            img.Dispose();
#endif
    }
}
