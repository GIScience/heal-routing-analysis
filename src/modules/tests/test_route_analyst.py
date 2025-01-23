#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for route analyst"""


from ..route_analyst.route import Route
from shapely.geometry import LineString


def test_as_dataframe():
    """Tests if route segments are extracted correctly"""
    coords = [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]]

    test_obj = Route({"geometry": {"coordinates": coords}})

    expected_segments_count = 5
    actual_segments_count = len(test_obj.as_dataframe())

    assert expected_segments_count == actual_segments_count

    expected_segment_4 = LineString([[3, 3], [4, 4]])
    actual_segment_4 = test_obj.as_dataframe().iloc[3]["geometry"]

    assert expected_segment_4 == actual_segment_4
