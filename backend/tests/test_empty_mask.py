import numpy as np
import pytest
from backend.segmentation.segmentation import mask_to_stl, EmptyMaskError


def test_empty_mask_raises(tmp_path):
    mask = np.zeros((10, 10, 10), dtype=np.uint8)
    out = tmp_path / "test.stl"
    with pytest.raises(EmptyMaskError):
        mask_to_stl(mask, spacing=(1.0, 1.0, 1.0), out_path=str(out))
