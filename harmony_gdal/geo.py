def clip_bbox(dataset_bounds, bbox):
    """Clips the bbox so it is no larger than the dataset.
    """
    bbox_bounds = [[bbox[0], bbox[2]], [bbox[1], bbox[3]]]

    x_intersections = latlon_intersection(dataset_bounds[0], bbox_bounds[0])
    y_intersections = latlon_intersection(dataset_bounds[1], bbox_bounds[1])

    if len(x_intersections) == 0 or len(y_intersections) == 0:
        return []

    return [[xi[0], yi[0], xi[1], yi[1]]
            for xi in x_intersections for yi in y_intersections]


def latlon_intersection(x, y):
    """Given a pair of latitude or longitude ranges, return their intersection,
    while also handling 'wraparound' at the antemeridian.
    """
    def expand(a):
        """Split a range into two if it wraps the antemeridian.
        """
        if a[1] < a[0]:
            return [[a[0], 180.0], [-180.0, a[1]]]
        else:
            return [a]

    intersections = [_range_intersection(a, b) for a in expand(x) for b in expand(y)]
    return [i for i in intersections if i]


def _range_intersection(a, b):
    """Returns whether two numeric ranges intersect.
    """
    if (b[0] <= (a[0] or a[1]) <= b[1]) or \
            (a[0] <= (b[0] or b[1]) <= a[1]):
        return [max(a[0], b[0]), min(a[1], b[1])]
    else:
        return []
