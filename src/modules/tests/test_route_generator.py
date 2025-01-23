#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for route generator"""


import rasterio as rio
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

from modules.route_generator import numpy2coords, search_nearby_pois


def test_numpy2coords():
    """
    Tests whether the numpy columns/rows are correctly transformed to geogr. coordinates
    :return:
    """
    transform = rio.transform.from_origin(10000000.0, 7000000.0, 250.0, 250.0)
    indices = np.arange(0, 20, 1).reshape(5, 4)
    selected_index = 0
    expected_x = 10000000.0 + 0.5 * 250
    expected_y = 7000000.0 + 0.5 * -250

    actual_x, actual_y = numpy2coords(indices, selected_index, transform)

    np.testing.assert_almost_equal(actual_x, expected_x, 1)
    np.testing.assert_almost_equal(actual_y, expected_y, 1)


def test_search_nearby_pois():
    """
    Tests whether the POIs are correctly selected in the buffer ring
    :return:
    """
    start_point = Point(0, 0)
    poi_df = gpd.GeoDataFrame({"id": [1, 2], "geometry": [Point(750, 0), Point(0, 350)]})
    max_distance1 = 1000
    min_distance1 = 300
    max_distance2 = 2000
    min_distance2 = 500
    max_distance3 = 2000
    min_distance3 = 1000

    expected_length1 = 2
    actual_result1 = search_nearby_pois(max_distance1, min_distance1, start_point, poi_df)
    actual_length1 = len(actual_result1)
    expected_length2 = 1
    actual_result2 = search_nearby_pois(max_distance2, min_distance2, start_point, poi_df)
    actual_length2 = len(actual_result2)
    expected_length3 = 0
    actual_result3 = search_nearby_pois(max_distance3, min_distance3, start_point, poi_df)
    actual_length3 = len(actual_result3)

    assert actual_length1 == expected_length1
    assert actual_length2 == expected_length2
    assert actual_length3 == expected_length3
