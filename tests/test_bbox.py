import pytest

from harmony_service_example.geo import clip_bbox, latlon_intersection, _range_intersection


def test_clip_identical():
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    bbox = [10.0, 40.0, 20.0, 45.0]

    assert clip_bbox(dataset_bounds, bbox) == [bbox]

def test_clip_larger_bbox():
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    bbox = [0.0, 15.0, 25.0, 49.0]
    expected = [[10.0, 40.0, 20.0, 45.0]]

    assert clip_bbox(dataset_bounds, bbox) == expected

def test_clip_non_intersecting_bbox():
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    bbox = [0.0, 5.0, 5.0, 9.0]
    expected = []

    assert clip_bbox(dataset_bounds, bbox) == expected

@pytest.mark.parametrize("bbox,expected", [
    ([11.0, 15.0, 25.0, 49.0], [[11.0, 40.0, 20.0, 45.0]]),
    ([0.0, 15.0, 19.0, 49.0], [[10.0, 40.0, 19.0, 45.0]]),
    ([0.0, 42.0, 25.0, 49.0], [[10.0, 42.0, 20.0, 45.0]]),
    ([0.0, 15.0, 25.0, 42.0], [[10.0, 40.0, 20.0, 42.0]]),
    ([11.0, 15.0, 12.0, 49.0], [[11.0, 40.0, 12.0, 45.0]]),
    ([0.0, 42.0, 25.0, 43.0], [[10.0, 42.0, 20.0, 43.0]]),
    ([11.0, 42.0, 12.0, 43.0], [[11.0, 42.0, 12.0, 43.0]])
])
def test_clip_intersecting_bbox(bbox, expected):
    dataset_bounds = ([10.0, 20.0], [40.0, 45.0])
    assert clip_bbox(dataset_bounds, bbox) == expected

@pytest.mark.parametrize("bbox,expected", [
    ([170.0, 40.0, -170.0, 50.0], [[175.0, 42.0, 180.0, 48.0], [-180.0, 42.0, -175.0, 48.0]]),
    ([178.0, 42.0, -178.0, 50.0], [[178.0, 42.0, 180.0, 48.0], [-180.0, 42.0, -178.0, 48.0]]),
    ([170.0, 44.0, -170.0, 46.0], [[175.0, 44.0, 180.0, 46.0], [-180.0, 44.0, -175.0, 46.0]]),
    ([179.0, 45.0, -179.0, 45.5], [[179.0, 45.0, 180.0, 45.5], [-180.0, 45.0, -179.0, 45.5]]),
])
def test_clip_antemeridian_dataset_spans(bbox, expected):
    dataset_bounds = ([175.0, -175.0], [42.0, 48.0])
    assert clip_bbox(dataset_bounds, bbox) == expected

@pytest.mark.parametrize("bbox,expected", [
    ([170.0, 40.0, -170.0, 50.0], [[175.0, 42.0, 179.0, 48.0]]),
    ([176.0, 44.0, -170.0, 46.0], [[176.0, 44.0, 179.0, 46.0]]),
])
def test_clip_antemeridian_dataset_east(bbox, expected):
    dataset_bounds = ([175.0, 179.0], [42.0, 48.0])
    assert clip_bbox(dataset_bounds, bbox) == expected

@pytest.mark.parametrize("bbox,expected", [
    ([170.0, 40.0, -170.0, 50.0], [[-179.0, 42.0, -175.0, 48.0]]),
])
def test_clip_antemeridian_dataset_west(bbox, expected):
    dataset_bounds = ([-179.0, -175.0], [42.0, 48.0])
    assert clip_bbox(dataset_bounds, bbox) == expected

@pytest.mark.parametrize("a,b,expected", [
    ([0, 1], [2, 3], []),
    ([0, 1], [0, 1], [[0, 1]]),
    ([0, 1], [0, 5], [[0, 1]]),
    ([0, 2], [1, 3], [[1, 2]]),
    ([1, 2], [0, 3], [[1, 2]]),
    ([1, 5], [170, 10], [[1, 5]]),
    ([-180, 0], [170, 0], [[-180, 0]]),
    ([0, 175], [170, -170], [[170, 175]]),
    ([170, -170], [175, -175], [[175, 180], [-180, -175]]),
    ([170, -170], [175, 179], [[175, 179]]),
    ([170, -170], [-179, -175], [[-179, -175]]),
    ([-90, 90], [45, -45], [[45, 90], [-90, -45]])
])
def test_latlon_intersection(a, b, expected):
    assert latlon_intersection(a, b) == latlon_intersection(b, a) == expected

@pytest.mark.parametrize("a,b,expected", [
    ([0, 1], [2, 3], []),
    ([-10, 10], [2, 3], [2, 3]),
    ([-10, 5], [-5, 10], [-5, 5])
])
def test_range_intersection(a, b, expected):
    assert _range_intersection(a, b) == _range_intersection(b, a) == expected
