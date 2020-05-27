def clip_bbox(dataset_bounds, bbox):
    """Clips the bbox so it is no larger than the dataset.
    """
    def normalize_lon_range(lon_min, lon_max):
        lon_min += 180.0
        lon_max += 180.0
        if lon_min > lon_max:
            lon_max += 360.0
        return (lon_min, lon_max)

    def denormalize_lon_range(lon_min, lon_max):
        if lon_max > 360.0:
            lon_max -= 360.0
        lon_min -= 180.0
        lon_max -= 180.0
        return (lon_min, lon_max)

    minx, maxx = normalize_lon_range(*dataset_bounds[0])
    miny, maxy = dataset_bounds[1]
    bbox_minx, bbox_miny, bbox_maxx, bbox_maxy = bbox
    bbox_minx, bbox_maxx = normalize_lon_range(bbox_minx, bbox_maxx)

    minx, maxx = denormalize_lon_range(max(minx, bbox_minx), min(maxx, bbox_maxx))
    return [
        minx, max(miny, bbox_miny),
        maxx, min(maxy, bbox_maxy)
    ]
