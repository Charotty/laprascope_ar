import numpy as np
from backend.segmentation.segmentation import simple_threshold_segmentation


def test_simple_threshold_segmentation():
    """Mask must be 1 inside threshold range and 0 outside."""
    arr = np.array([[[0, 50, 150], [40, 300, 400]]])  # shape (1,2,3)
    mask = simple_threshold_segmentation(arr, threshold=(30, 300))

    # Positions expected to be 1: 50, 40, 150, 300
    expected = np.array([[[0, 1, 1], [1, 1, 0]]], dtype=np.uint8)
    assert np.array_equal(mask, expected)
