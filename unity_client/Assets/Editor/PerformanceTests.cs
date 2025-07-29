using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

public class PerformanceTests {
    private GameObject _fpsObj;
    private FPSMonitor _monitor;

    [UnitySetUp]
    public IEnumerator SetUp() {
        _fpsObj = new GameObject("FPSMonitor", typeof(FPSMonitor));
        _monitor = _fpsObj.GetComponent<FPSMonitor>();
        yield return null;
    }

    [UnityTest]
    public IEnumerator AverageFPS_ShouldBeAboveThreshold() {
        // Wait 300 frames (~5 seconds at 60 FPS)
        for (int i = 0; i < 300; i++) {
            yield return null;
        }
        Debug.Log($"Average FPS during test: {_monitor.AverageFPS}");
        Assert.GreaterOrEqual(_monitor.AverageFPS, 45f, "Average FPS is below 45");
    }

    [UnityTearDown]
    public IEnumerator TearDown() {
        Object.Destroy(_fpsObj);
        yield return null;
    }
}
