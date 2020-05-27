import pytest

from harmony_gdal.geo import clip_bbox

def test_clip_identical():
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    bbox = [10.0, 40.0, 20.0, 45.0]
    
    actual = clip_bbox(dataset_bounds, bbox)
    
    assert actual == bbox

def test_clip_larger_bbox():
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    bbox = [0.0, 15.0, 25.0, 49.0]
    expected = [10.0, 40.0, 20.0, 45.0]
    
    actual = clip_bbox(dataset_bounds, bbox)
    
    assert actual == expected

@pytest.mark.parametrize("bbox,expected", [
    ([11.0, 15.0, 25.0, 49.0], [11.0, 40.0, 20.0, 45.0]),
    ([0.0, 15.0, 19.0, 49.0], [10.0, 40.0, 19.0, 45.0]),
    ([0.0, 42.0, 25.0, 49.0], [10.0, 42.0, 20.0, 45.0]),
    ([0.0, 15.0, 25.0, 42.0], [10.0, 40.0, 20.0, 42.0]),
    ([11.0, 15.0, 12.0, 49.0], [11.0, 40.0, 12.0, 45.0]),
    ([0.0, 42.0, 25.0, 43.0], [10.0, 42.0, 20.0, 43.0]),
    ([11.0, 42.0, 12.0, 43.0], [11.0, 42.0, 12.0, 43.0])
])
def test_clip_intersecting_bbox(bbox, expected):
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    
    actual = clip_bbox(dataset_bounds, bbox)
    
    assert actual == expected
