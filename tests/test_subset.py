"""Crop real rasters without accumulating earlier GDAL arguments."""

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
import pystac
from harmony_service_lib.message import Message
from osgeo import gdal, osr

from harmony_service_example import transform
from harmony_service_example.transform import HarmonyAdapter


@pytest.fixture
def raster(tmp_path):
    path = tmp_path / "input with spaces.tif"
    values = np.arange(20 * 360, dtype=np.int16).reshape(20, 360) + 1
    dataset = gdal.GetDriverByName("GTiff").Create(
        str(path), 360, 20, 1, gdal.GDT_Int16
    )
    dataset.SetGeoTransform((-180, 1, 0, 10, 0, -1))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    dataset.SetProjection(srs.ExportToWkt())
    dataset.GetRasterBand(1).WriteArray(values)
    dataset = None
    return path, values


def _adapter(bbox):
    return HarmonyAdapter(Message({"subset": {"bbox": list(map(float, bbox))}}))


@pytest.mark.parametrize("bbox", [
    [170, -5, -170, 5], [178, -3, -177, 4],
    [160, -10, -165, 10], [179, 0, -179, 1],
])
def test_antimeridian_parts_are_cropped_independently(raster, tmp_path, bbox):
    source, values = raster
    original = source.read_bytes()
    adapter = _adapter(bbox)
    adapter.cmd = Mock(wraps=adapter.cmd)
    output = adapter.subset("group/temperature", str(source), str(tmp_path))
    west, south, east, north = bbox
    parts = [(west, 180), (-180, east)]
    crop_calls = adapter.cmd.call_args_list[:2]
    assert len(adapter.cmd.call_args_list) == 3
    for index, ((left, right), call) in enumerate(zip(parts, crop_calls)):
        expected_path = tmp_path / (
            "group_temperature__%s_subsetted.tif" % index
        )
        assert call.args == (
            "gdal_translate", "-of", "GTiff", "-projwin",
            str(float(left)), str(float(north)),
            str(float(right)), str(float(south)),
            str(source), str(expected_path),
        )
        part = gdal.Open(str(expected_path))
        np.testing.assert_array_equal(
            part.ReadAsArray(),
            values[10 - north:10 - south, left + 180:right + 180],
        )
        assert part.GetGeoTransform() == (left, 1, 0, north, 0, -1)
        part = None
    merged = gdal.Open(output)
    expected = np.zeros((north - south, 360), dtype=np.int16)
    expected[:, west + 180:] = values[10 - north:10 - south, west + 180:]
    expected[:, :east + 180] = values[10 - north:10 - south, :east + 180]
    np.testing.assert_array_equal(merged.ReadAsArray(), expected)
    assert merged.GetGeoTransform() == (-180, 1, 0, north, 0, -1)
    merged = None
    assert source.read_bytes() == original
    assert output == str(tmp_path / "group_temperature__subsetted.tif")


@pytest.mark.parametrize("bbox", [[5, -4, 12, 4], [-200, -5, -170, 5]])
def test_single_crop_remains_unchanged(raster, tmp_path, bbox):
    source, values = raster
    adapter = _adapter(bbox)
    adapter.cmd = Mock(wraps=adapter.cmd)
    result = adapter.subset("temperature", str(source), str(tmp_path))
    left, south, right, north = bbox
    left = max(-180, left)
    dataset = gdal.Open(result)
    np.testing.assert_array_equal(
        dataset.ReadAsArray(),
        values[10 - north:10 - south, left + 180:right + 180],
    )
    dataset = None
    assert adapter.cmd.call_count == 1


@pytest.mark.parametrize("subset", [None, {}, {"bbox": None}])
def test_disabled_subset_does_not_access_raster(tmp_path, subset):
    adapter = HarmonyAdapter(Message({"subset": subset}))
    adapter.cmd = Mock(side_effect=AssertionError("must not invoke GDAL"))
    source = str(tmp_path / "not-created.tif")
    assert adapter.subset("temperature", source, str(tmp_path)) == source
    adapter.cmd.assert_not_called()


def test_second_crop_error_propagates_without_merging(raster, tmp_path):
    source, _ = raster
    adapter = _adapter([170, -5, -170, 5])
    error = subprocess.CalledProcessError(1, ["gdal_translate"])
    adapter.cmd = Mock(side_effect=[[], error])
    with pytest.raises(subprocess.CalledProcessError) as caught:
        adapter.subset("temperature", str(source), str(tmp_path))
    assert caught.value is error
    assert adapter.cmd.call_count == 2


def test_process_item_stages_both_sides_and_cleans_temporary_files(
    raster, tmp_path, monkeypatch
):
    source, values = raster
    original_bytes = source.read_bytes()
    message = Message({
        "version": "0.22.0",
        "subset": {"bbox": [170, -5, -170, 5]},
        "format": {"mime": "image/tiff"},
        "sources": [{"collection": "fixture", "variables": [
            {"name": "temperature", "fullPath": "temperature"}
        ]}],
        "stagingLocation": "s3://unused-fixture/",
    })
    adapter = HarmonyAdapter(message)
    item = pystac.Item("fixture", None, [-180, -10, 180, 10],
                       datetime(2020, 1, 1, tzinfo=timezone.utc), {})
    item.add_asset("data", pystac.Asset(
        "https://example.invalid/input.tif",
        media_type="image/tiff", roles=["data"]
    ))
    staged = tmp_path / "staged.tif"
    downloaded = []

    def local_download(href, output_dir, **kwargs):
        assert href == item.assets["data"].href
        destination = Path(output_dir) / "input.tif"
        shutil.copyfile(source, destination)
        downloaded.append(destination)
        return str(destination)

    def local_stage(filename, output_filename, mime, **kwargs):
        assert mime == "image/tiff"
        shutil.copyfile(filename, staged)
        return staged.as_uri()

    monkeypatch.setattr(transform, "download", local_download)
    monkeypatch.setattr(transform, "stage", local_stage)
    result = adapter.process_item(item, message.sources[0])
    assert result is not item
    assert result.assets["data"].href == staged.as_uri()
    assert result.assets["data"].media_type == "image/tiff"
    dataset = gdal.Open(str(staged))
    expected = np.zeros((10, 360), dtype=np.int16)
    expected[:, :10] = values[5:15, :10]
    expected[:, 350:] = values[5:15, 350:]
    np.testing.assert_array_equal(dataset.ReadAsArray(), expected)
    dataset = None
    assert len(downloaded) == 1
    assert not downloaded[0].parent.exists()
    assert source.read_bytes() == original_bytes
    assert item.assets["data"].href == "https://example.invalid/input.tif"


def test_nonintersecting_subset_keeps_existing_rejection(raster, tmp_path):
    source, _ = raster
    adapter = _adapter([20, 30, 40, 50])
    adapter.cmd = Mock(side_effect=AssertionError("must not invoke GDAL"))
    with pytest.raises(AssertionError):
        adapter.subset("temperature", str(source), str(tmp_path))
    adapter.cmd.assert_not_called()
