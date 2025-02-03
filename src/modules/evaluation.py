#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compare and evaluate groups of routes"""


import geopandas as gpd
import json
import logging
import numpy as np
import pandas as pd
import warnings
from shapely import wkt
from tqdm import tqdm

from modules.route_analyst.route import Route

# ignore FutureWarnings from geopandas
warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.filterwarnings(action="ignore", message=".*initial implementation of Parquet.*")
# ignore SettingWithCopyWarning from (geo-)pandas
pd.options.mode.chained_assignment = None  # default='warn'


def generate_route_statistics(
    logger,
    solar_data,
    route_i,
    solar_i,
    time_of_day,
    time_of_day_values,
    default_route_obj,
    default_type,
    route_obj,
    optimized_type,
):
    """Calculates statistics in comparison of optimized to default routes"""

    distance = route_obj.distance
    duration = route_obj.duration
    geometry = route_obj.geometry
    solar_exposure = route_obj.solar_exposure

    len_diff_meter = route_obj.length_diff_meter(default_route_obj)
    len_diff_rel = route_obj.length_diff_rel(default_route_obj)
    dur_diff_sec = route_obj.duration_diff_sec(default_route_obj)
    dur_diff_rel = route_obj.duration_diff_rel(default_route_obj)
    same_ratio = route_obj.same_ratio(default_route_obj)
    avoided_ratio = route_obj.avoided_ratio(default_route_obj)
    detour_ratio = route_obj.detour_ratio(default_route_obj)
    geom_diff = route_obj.geom_difference(default_route_obj)
    geom_intersect = route_obj.geom_intersection(default_route_obj)

    if time_of_day == time_of_day_values[0]:

        assert (
            time_of_day_values[0] == default_type
        ), f"Error: first entry of time_of_day_values does not match {default_type}!"

        append_route_data = {
            "trip_id": route_i,
            "route_type": f"{time_of_day_values[0]} route",
            f"sol_expo_{time_of_day_values[1]}": round(solar_data[solar_i][time_of_day_values[1]], 2),
            f"sol_expo_{time_of_day_values[2]}": round(solar_data[solar_i][time_of_day_values[2]], 2),
            f"sol_expo_{time_of_day_values[3]}": round(solar_data[solar_i][time_of_day_values[3]], 2),
            f"sol_expo_{time_of_day_values[4]}": round(solar_data[solar_i][time_of_day_values[4]], 2),
            "sol_expo_diff_abs": np.nan,
            "sol_expo_diff_rel": np.nan,
            "sol_expo_reduction": np.nan,
            "distance": round(distance),
            "len_diff_meter": np.nan,
            "len_diff_rel": np.nan,
            "duration": round(duration),
            "dur_diff_sec": np.nan,
            "dur_diff_perc": np.nan,
            "same_ratio": np.nan,
            "avoided_ratio": np.nan,
            "detour_ratio": np.nan,
            "geom": geometry,
            "geom_diff": np.nan,
            "geom_intersect": np.nan,
        }
    else:
        sol_expo_diff_abs = solar_exposure - solar_data[solar_i][time_of_day]
        if solar_data[solar_i][time_of_day] == 0:
            try:
                assert solar_exposure == solar_data[solar_i][time_of_day]
                sol_expo_diff_rel = 0
                sol_expo_reduction = 0
            except AssertionError:
                logger.warning(
                    f"Warning during solar exposure difference calculation: solar exposure of {default_type} route with id {route_i} is zero, value of {time_of_day} does not match. Setting to nan."
                )
                sol_expo_diff_rel = np.nan
                sol_expo_reduction = np.nan
        else:
            sol_expo_diff_rel = (
                (solar_exposure - solar_data[solar_i][time_of_day]) / solar_data[solar_i][time_of_day] * 100
            )  # relative difference between solar exposure of optimized and default route
            sol_expo_reduction = (
                1 - (solar_exposure / solar_data[solar_i][time_of_day])
            ) * 100  # how much less (relative) sol expo in % compared to default route

        append_route_data = {
            "trip_id": route_i,
            "route_type": f"{optimized_type} route at {time_of_day}",
            f"sol_expo_{time_of_day}": round(solar_exposure, 2),
            "sol_expo_diff_abs": round(sol_expo_diff_abs, 2),
            "sol_expo_diff_rel": round(sol_expo_diff_rel, 2),
            "sol_expo_reduction": round(sol_expo_reduction, 2),
            "distance": round(distance),
            "len_diff_meter": round(len_diff_meter),
            "len_diff_rel": round(len_diff_rel, 2),
            "duration": round(duration),
            "dur_diff_sec": round(dur_diff_sec),
            "dur_diff_perc": round(dur_diff_rel, 2),
            "same_ratio": round(same_ratio, 2),
            "avoided_ratio": round(avoided_ratio, 2),
            "detour_ratio": round(detour_ratio, 2),
            "geom": geometry,
            "geom_diff": str(geom_diff),
            "geom_intersect": str(geom_intersect),
        }

    return append_route_data


def rank_segments(solar_threshold_dict, default_route_geometry, default_type, segment_geometry, segment_csv):
    """Ranks the segments based on the solar exposure and the solar threshold in comparison to the default route"""
    if segment_geometry != default_type:
        # check if segment is within default route
        naming = "equal" if segment_geometry.within(default_route_geometry) else "detour"
    else:
        naming = default_type

    # low solar exposure
    if segment_csv < solar_threshold_dict["low"]:
        ranking = f"{naming}, solar exposure < {solar_threshold_dict['low']} %"
    # mid solar exposure
    elif solar_threshold_dict["low"] <= segment_csv < solar_threshold_dict["high"]:
        ranking = (
            f"{naming}, {solar_threshold_dict['low']} % <= solar exposure < {solar_threshold_dict['high']} %"
        )
    # high solar exposure
    else:
        ranking = f"{naming}, {solar_threshold_dict['high']} % >= solar exposure"
    return ranking


def generate_segment_data(
    segments_sol_data,
    solar_threshold_dict,
    trip_id,
    default_data_i,
    time_of_day,
    time_of_day_values,
    default_route_geometry,
    default_type,
    segment,
    segment_id,
    optimized_type,
):
    """Splits the route geometry into segments and ranks the segments"""

    if time_of_day == time_of_day_values[0]:

        append_segment_data = {
            "trip_id": trip_id,
            "route_type": f"{time_of_day_values[0]} route",
            "segment_id": segment_id,
            f"sol_expo_{time_of_day_values[1]}": segments_sol_data[default_data_i][time_of_day_values[1]][
                segment_id
            ],
            f"sol_expo_{time_of_day_values[2]}": segments_sol_data[default_data_i][time_of_day_values[2]][
                segment_id
            ],
            f"sol_expo_{time_of_day_values[3]}": segments_sol_data[default_data_i][time_of_day_values[3]][
                segment_id
            ],
            f"sol_expo_{time_of_day_values[4]}": segments_sol_data[default_data_i][time_of_day_values[4]][
                segment_id
            ],
            f"ranking_{time_of_day_values[1]}": rank_segments(
                solar_threshold_dict,
                default_route_geometry,
                default_type,
                time_of_day_values[0],
                segments_sol_data[default_data_i][time_of_day_values[1]][segment_id],
            ),
            f"ranking_{time_of_day_values[2]}": rank_segments(
                solar_threshold_dict,
                default_route_geometry,
                default_type,
                time_of_day_values[0],
                segments_sol_data[default_data_i][time_of_day_values[2]][segment_id],
            ),
            f"ranking_{time_of_day_values[3]}": rank_segments(
                solar_threshold_dict,
                default_route_geometry,
                default_type,
                time_of_day_values[0],
                segments_sol_data[default_data_i][time_of_day_values[3]][segment_id],
            ),
            f"ranking_{time_of_day_values[4]}": rank_segments(
                solar_threshold_dict,
                default_route_geometry,
                default_type,
                time_of_day_values[0],
                segments_sol_data[default_data_i][time_of_day_values[4]][segment_id],
            ),
            "segtype": np.nan,
            "geom": segment["geometry"],
        }
    else:
        ranking = rank_segments(
            solar_threshold_dict, default_route_geometry, default_type, segment["geometry"], segment["csv"]
        )
        segtype = ranking.split(",")[0]

        append_segment_data = {
            "trip_id": trip_id,
            "route_type": f"{optimized_type} route at {time_of_day}",
            "segment_id": segment_id,
            f"sol_expo_{time_of_day}": segment["csv"],
            f"ranking_{time_of_day}": ranking,
            "segtype": segtype,
            "geom": segment["geometry"],
        }

    return append_segment_data


def split_in_types(
    gdf, out_dir_dict, filetype, time_of_day_values, optimized_type, standardization_factor, sorted_geom_name
):
    """Split statistics file into routes with specific times of day"""

    route_type_list = [
        f"{time_of_day_values[0]} route",
        f"{optimized_type} route at {time_of_day_values[1]}",
        f"{optimized_type} route at {time_of_day_values[2]}",
        f"{optimized_type} route at {time_of_day_values[3]}",
        f"{optimized_type} route at {time_of_day_values[4]}",
    ]

    for time_of_day, route_type in zip(time_of_day_values, route_type_list):
        logging.info(f"Processing {time_of_day}...")
        gdf_time_of_day = gdf.loc[gdf.route_type == route_type]
        gdf_time_of_day.to_feather(out_dir_dict[f"data_{filetype}"] / f"{filetype}_{time_of_day}.feather")
        # Optimized routes
        if filetype == "segments" and time_of_day != time_of_day_values[0]:
            for segtype in ["detour", "equal"]:
                gdf_ex = gdf.loc[gdf.segtype == segtype]
                if gdf_ex.empty:
                    return
                aggregate_count(
                    gdf_ex,
                    out_dir_dict["aggregation"],
                    segtype,
                    time_of_day,
                    time_of_day_values,
                    standardization_factor,
                    sorted_geom_name,
                )
        # Default routes
        if filetype == "segments" and time_of_day == time_of_day_values[0]:
            aggregate_count(
                gdf_time_of_day,
                out_dir_dict["aggregation"],
                "alltimes",
                time_of_day,
                time_of_day_values,
                standardization_factor,
                sorted_geom_name,
            )


def format_segments(segment):
    """Convert segment geometries to strings and sorts the coordinates for equality comparison"""
    coords = list(segment.coords)
    sorted_coords = sorted(coords, key=lambda x: (x[0], x[1]))
    coord_strs = [f"{x} {y} {z}" for x, y, z in sorted_coords]

    return f"LINESTRING Z ({', '.join(coord_strs)})"


def wkt_loads(row, col):
    """Convert WKT string to geometry"""
    try:
        return wkt.loads(row[col])
    except Exception:
        return None


def aggregate_count(
    gdf, out_folder, segtype, time_of_day, time_of_day_values, standardization_factor, sorted_geom_name
):
    """Aggregate segments per time of day and rank by count"""
    if time_of_day == time_of_day_values[0]:
        col_list = [
            sorted_geom_name,
            "route_type",
            f"sol_expo_{time_of_day_values[1]}",
            f"sol_expo_{time_of_day_values[2]}",
            f"sol_expo_{time_of_day_values[3]}",
            f"sol_expo_{time_of_day_values[4]}",
            f"ranking_{time_of_day_values[1]}",
            f"ranking_{time_of_day_values[2]}",
            f"ranking_{time_of_day_values[3]}",
            f"ranking_{time_of_day_values[4]}",
        ]
    else:
        col_list = [sorted_geom_name, "route_type", f"sol_expo_{time_of_day}", f"ranking_{time_of_day}"]

    gdf[sorted_geom_name] = gdf["geom"].apply(format_segments)

    counts = gdf.groupby(col_list).size().reset_index(name="count")
    counts = counts.sort_values(by="count", ascending=False)
    counts["count_standardized"] = counts.apply(
        lambda row: (row["count"] / standardization_factor) * 100, axis=1
    )
    counts["geom"] = counts.apply(wkt_loads, col=sorted_geom_name, axis=1)
    counts = gpd.GeoDataFrame(counts)
    counts.set_geometry(col="geom", inplace=True)
    counts.set_crs("EPSG:4326", inplace=True)
    counts.to_feather(out_folder / f"counts_{time_of_day}_{segtype}.feather")


def write_gdf(in_data, outname, out_dir_dict):
    """Export GeoDataFrame to file"""
    gdf_full = gpd.GeoDataFrame(in_data)
    gdf_full.set_geometry(col="geom", inplace=True)
    gdf_full.set_crs("EPSG:4326", inplace=True)
    gdf_full.to_feather(out_dir_dict["out_dir"] / f"{outname}.feather")

    return gdf_full


def evaluate_routes(
    n_trips,
    solar_threshold_dict,
    poi_type_list,
    time_of_day_dict,
    default_type,
    optimized_type,
    out_dir_dict,
    route_level_filename,
    segment_level_filename,
    bar,
):
    """Extracts information about route objects"""

    logger = logging.getLogger(__file__)

    routes_list_full = []
    segments_list_full = []
    sorted_geom_name = "geom_str_sorted"

    routes_sol_data_file = out_dir_dict["exportdata"] / f"{default_type}_routes_sol_data.json"
    with open(routes_sol_data_file) as f_routes_sol_data:
        routes_sol_data = json.load(f_routes_sol_data)
    segments_sol_data_file = out_dir_dict["exportdata"] / f"{default_type}_segments_sol_data.json"
    with open(segments_sol_data_file) as f_segments_sol_data:
        segments_sol_data = json.load(f_segments_sol_data)

    time_of_day_values = [default_type] + list(
        time_of_day_dict.values()
    )  # include default folder (iterate through all folders)

    total_routes = n_trips * len(poi_type_list)

    with bar.pause():
        for trip_id in tqdm(range(1, total_routes + 1), leave=False):
            # read default type route as comparison basis
            default_path = out_dir_dict["data_routes"] / default_type
            default_item = list(default_path.glob(f"routes_{default_type}_{trip_id}_*.geojson"))[0]
            with open(default_item) as f:
                default_data = json.load(f)
                default_route_obj = Route(default_data)
                default_route_geometry = default_route_obj.geometry

            for time_of_day in time_of_day_values:
                # read current route to compare to default route
                item_path = out_dir_dict["data_routes"] / time_of_day
                item = list(item_path.glob(f"routes_*_{trip_id}_*.geojson"))[0]
                with open(item) as f:
                    data = json.load(f)
                    route_obj = Route(data)
                    route_segments = route_obj.as_dataframe()

                    default_data_i = trip_id - 1

                    route_append_data = generate_route_statistics(
                        logger,
                        routes_sol_data,
                        trip_id,
                        default_data_i,
                        time_of_day,
                        time_of_day_values,
                        default_route_obj,
                        default_type,
                        route_obj,
                        optimized_type,
                    )
                    routes_list_full.append(route_append_data)

                    for segment_id in range(len(route_segments)):
                        segment = route_segments.iloc[segment_id]
                        segments_append_data = generate_segment_data(
                            segments_sol_data,
                            solar_threshold_dict,
                            trip_id,
                            default_data_i,
                            time_of_day,
                            time_of_day_values,
                            default_route_geometry,
                            default_type,
                            segment,
                            segment_id,
                            optimized_type,
                        )
                        segments_list_full.append(segments_append_data)
                # remove current route file and folder if empty
                item.unlink()
                try:
                    item.parents[0].rmdir()
                except (FileNotFoundError, OSError):
                    pass

    # statistics export
    logger.info("Generating resulting files...")
    logger.info("Routes...")
    route_level_data = write_gdf(routes_list_full, route_level_filename, out_dir_dict)
    routes_gdf_length = len(route_level_data)
    standardization_factor = routes_gdf_length / len(time_of_day_values)
    del routes_list_full  # prevent memory leak
    split_in_types(
        route_level_data,
        out_dir_dict,
        "routes",
        time_of_day_values,
        optimized_type,
        standardization_factor,
        sorted_geom_name,
    )
    del route_level_data  # prevent memory leak

    logger.info("Segments...")
    segment_level_data = write_gdf(segments_list_full, segment_level_filename, out_dir_dict)
    del segments_list_full  # prevent memory leak
    logger.info("Postprocessing per times of day...")
    split_in_types(
        segment_level_data,
        out_dir_dict,
        "segments",
        time_of_day_values,
        optimized_type,
        standardization_factor,
        sorted_geom_name,
    )
