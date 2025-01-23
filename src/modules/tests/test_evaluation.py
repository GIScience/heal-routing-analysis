#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for evaluation"""


from ..route_analyst.route import Route
from ..evaluation import rank_segments
from shapely.geometry import LineString
import geopandas as gpd


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


def test_rank_segments():
    """
    Test if segments are ranked correctly
    :return:
    """
    solar_threshold_dict = {"low": 25, "high": 60}
    normal_segments = gpd.GeoDataFrame(
        {
            "geometry": [
                LineString([[0, 0], [1, 1]]),
                LineString([[1, 1], [2, 2]]),
                LineString([[2, 2], [3, 3]]),
                LineString([[3, 3], [4, 4]]),
            ]
        }
    )
    segment1_df = gpd.GeoDataFrame({"geometry": LineString([[0, 0], [1, 1]]), "csv": 100}, index=[0])
    segment1 = segment1_df.iloc[0]
    segment2_df = gpd.GeoDataFrame({"geometry": LineString([[1, 1], [1, 2]]), "csv": 60}, index=[0])
    segment2 = segment2_df.iloc[0]
    segment3_df = gpd.GeoDataFrame({"geometry": LineString([[1, 2], [3, 3]]), "csv": 30}, index=[0])
    segment3 = segment3_df.iloc[0]
    segment4_df = gpd.GeoDataFrame({"geometry": LineString([[3, 3], [4, 4]]), "csv": 24}, index=[0])
    segment4 = segment4_df.iloc[0]

    expected_ranking1 = f"equal, {solar_threshold_dict['high']} % >= solar exposure area"
    expected_ranking2 = f"detour, {solar_threshold_dict['high']} % >= solar exposure area"
    expected_ranking3 = (
        f"detour, {solar_threshold_dict['low']} % <= solar exposure area < {solar_threshold_dict['high']} %"
    )
    expected_ranking4 = f"equal, solar exposure area < {solar_threshold_dict['low']} %"
    actual_ranking1 = rank_segments(
        solar_threshold_dict, normal_segments, segment1["geometry"], segment1["csv"]
    )
    actual_ranking2 = rank_segments(
        solar_threshold_dict, normal_segments, segment2["geometry"], segment2["csv"]
    )
    actual_ranking3 = rank_segments(
        solar_threshold_dict, normal_segments, segment3["geometry"], segment3["csv"]
    )
    actual_ranking4 = rank_segments(
        solar_threshold_dict, normal_segments, segment4["geometry"], segment4["csv"]
    )

    assert expected_ranking1 == actual_ranking1
    assert expected_ranking2 == actual_ranking2
    assert expected_ranking3 == actual_ranking3
    assert expected_ranking4 == actual_ranking4
