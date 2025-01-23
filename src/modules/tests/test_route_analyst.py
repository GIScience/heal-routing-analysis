#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for route analyst"""


from shapely.geometry import LineString

from modules.route_analyst.route import Route


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


def test_calc_solar_exposure():
    """
    Test if solar exposure value is calculated correctly
    :return:
    """
    test_obj = Route(
        {
            "properties": {
                "extras": {
                    "csv": {
                        "summary": [
                            {"value": 10.0, "distance": 1000, "amount": 0},
                            {"value": 30.0, "distance": 1000, "amount": 0},
                            {"value": 50.0, "distance": 1000, "amount": 0},
                        ]
                    }
                }
            }
        }
    )

    expected_solar_expo = 30  # (10 * 1000 + 30 * 1000 + 50 * 1000) / 3000
    actual_solar_expo = test_obj.solar_exposure

    assert expected_solar_expo == actual_solar_expo


def test_calc_length_diff_rel():
    """
    Test if distance difference percent value is calculated correctly
    :return:
    """
    test_obj = Route(
        {
            "properties": {
                "summary": {"distance": 300},
            }
        }
    )

    normal_test_obj = Route(
        {
            "properties": {
                "summary": {"distance": 100},
            }
        }
    )

    expected_dist_diff = 200  # (300 - 100) / 100 * 100
    actual_dist_diff = test_obj.length_diff_rel(normal_test_obj)

    assert expected_dist_diff == actual_dist_diff


def test_calc_geometry_stats():
    """
    Test if geometry statistics for the different parts of the route are calculated correctly
    :return:
    """
    test_obj = Route(
        {
            "geometry": {
                "coordinates": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [2.0, 1.0], [2.0, 2.0], [3.0, 2.0]],
            }
        }
    )

    normal_test_obj = Route(
        {
            "geometry": {
                "coordinates": [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 1.0], [2.0, 2.0], [3.0, 2.0]],
            }
        }
    )

    expected_same_ratio = 60
    actual_same_ratio = test_obj.same_ratio(normal_test_obj)

    expected_avoided_ratio = 40
    actual_avoided_ratio = test_obj.avoided_ratio(normal_test_obj)

    expected_detour_ratio = 40
    actual_detour_ratio = test_obj.detour_ratio(normal_test_obj)

    assert expected_same_ratio == actual_same_ratio
    assert expected_avoided_ratio == actual_avoided_ratio
    assert expected_detour_ratio == actual_detour_ratio
