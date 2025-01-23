#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for evaluation"""


from shapely.geometry import LineString

from modules.evaluation import rank_segments, format_segments


def test_rank_segments():
    """
    Test if segments are ranked correctly
    :return:
    """
    solar_threshold_dict = {"low": 25, "high": 60}
    default_route_geometry = LineString([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]])
    default_type = "default"

    segment1_geometry = LineString([[0, 0], [1, 1]])
    segment1_csv = 100
    segment2_geometry = LineString([[1, 1], [1, 2]])
    segment2_csv = 60
    segment3_geometry = LineString([[1, 2], [3, 3]])
    segment3_csv = 30
    segment4_geometry = LineString([[3, 3], [4, 4]])
    segment4_csv = 24

    expected_ranking1 = f"equal, {solar_threshold_dict['high']} % >= solar exposure"
    expected_ranking2 = f"detour, {solar_threshold_dict['high']} % >= solar exposure"
    expected_ranking3 = (
        f"detour, {solar_threshold_dict['low']} % <= solar exposure < {solar_threshold_dict['high']} %"
    )
    expected_ranking4 = f"equal, solar exposure < {solar_threshold_dict['low']} %"

    actual_ranking1 = rank_segments(
        solar_threshold_dict, default_route_geometry, default_type, segment1_geometry, segment1_csv
    )
    actual_ranking2 = rank_segments(
        solar_threshold_dict, default_route_geometry, default_type, segment2_geometry, segment2_csv
    )
    actual_ranking3 = rank_segments(
        solar_threshold_dict, default_route_geometry, default_type, segment3_geometry, segment3_csv
    )
    actual_ranking4 = rank_segments(
        solar_threshold_dict, default_route_geometry, default_type, segment4_geometry, segment4_csv
    )

    assert expected_ranking1 == actual_ranking1
    assert expected_ranking2 == actual_ranking2
    assert expected_ranking3 == actual_ranking3
    assert expected_ranking4 == actual_ranking4


def test_format_segments():
    """
    Test if segment geometries are formatted correctly
    :return:
    """
    segment1 = LineString([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    segment2 = LineString([(2, 2, 2), (0, 0, 0), (1, 1, 1)])

    expected_format1 = "LINESTRING Z (0.0 0.0 0.0, 1.0 1.0 1.0, 2.0 2.0 2.0)"
    expected_format2 = "LINESTRING Z (0.0 0.0 0.0, 1.0 1.0 1.0, 2.0 2.0 2.0)"

    actual_format1 = format_segments(segment1)
    actual_format2 = format_segments(segment2)

    assert expected_format1 == actual_format1
    assert expected_format2 == actual_format2
