#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate usual and HEAL routes"""


from modules.route_analyst.client import RoutingClient
import modules.utils as utils

import copy
import logging
import requests
import subprocess
import sys
import pyproj
import json

import geopandas as gpd
import numpy as np
import rasterio as rio
import rasterio.mask as mask
from shapely.geometry import Point
from shapely.ops import transform


def search_nearby_pois(max_distance, min_distance, start_point_utm, poi_df):
    """
    Creates a ring buffer area around the start point and selects all POIs within this area
    :param max_distance: maximum distance from start point
    :param min_distance: minimum distance from start point
    :param poi_df: dataframe with POIs
    :param start_point_utm: start point in utm coordinates
    :return: dataframe with POIs within the buffer zone
    """
    bufferzone = start_point_utm.buffer(max_distance - 250).difference(start_point_utm.buffer(min_distance))
    nearby_pois = poi_df.loc[poi_df.intersects(bufferzone)]
    return nearby_pois


def reproject_geometry(geom, from_crs: str, to_crs: str):
    """
    Reprojects an object to another crs
    :param geom: Geometry object
    :param from_crs: crs of object
    :param to_crs: target crs
    :return: reprojected geometry
    """
    from_crs = pyproj.CRS(from_crs)
    to_crs = pyproj.CRS(to_crs)
    project = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True).transform
    new_geom = transform(project, geom)
    return new_geom


def StartPointGenerator(logger, data_dir, pop_file, aoi_data):
    """
    Generator which yields random start points based on population density
    :param pop_file: Raster file with population data
    :param aoi_file: Vector file containing area of interest (aoi), uses only the first feature [0]
    :param n: number of points to generate (to be implemented)
    :return: tuple of coordinates
    """
    aoi = aoi_data["geometry"]

    # call preprocess to clip and reproject
    pop_file_clip_reproj = preprocess(logger, data_dir, pop_file, aoi)

    with rio.open(pop_file_clip_reproj) as src:
        population = src.read(1)
        new_transform = src.transform  # rio.windows.transform(window, src.transform)
        nodata = src.nodata
    population = np.where((population == nodata) | (population < 0), 0, population)
    prob = population / population.sum()

    # generate a new start point every time next() is called in generate_routes()
    while True:  # infinite loop, exit points are defined in generate_routes()
        # select random pixel of raster
        start_point = Point(*select_pixel(prob, new_transform))
        # Check if point is within aoi
        valid_start_point = start_point.within(aoi[0])
        if valid_start_point is not None:
            yield start_point
        else:
            continue


def preprocess(logger, data_dir, pop_file, aoi):
    """
    Clip population raster file with AOI vector file generate new population output file as TIF
    :param in_raster: Raster file with population data
    :param in_shape: Vector file containing area of interest (aoi)
    :return: writes a new tif file to disk and returns its path
    """
    out_clip = data_dir / "pop_file_clipped.tif"
    out_raster = data_dir / "pop_file_clip_proj.tif"
    # clip raster
    try:
        # open the raster in reading mode to be able to write the info to a new raster file
        with rio.open(pop_file, "r") as src:
            aoi_reproj = aoi.to_crs(src.crs)
            out_image, out_transform = mask.mask(src, aoi_reproj, crop=True)
            # take the metadata of the original rasterfile
            out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "dtype": "float64",
                "nodata": 0,
            }
        )
        # write raster file with new info to file
        with rio.open(out_clip, "w", **out_meta) as dest:
            dest.write(out_image)
    except Exception as e:
        logger.exception(f"ERROR: unable to clip raster with shapefile: {e}")
        sys.exit(1)
    # reproject raster
    try:
        subprocess.call(
            f"rio warp {out_clip} --dst-crs EPSG:4326 --dst-nodata 0 -o {out_raster} --overwrite",
            shell=True,
            stdout=subprocess.DEVNULL,
        )  # hardcode
        logger.info("Population file was successfully preprocessed.")
    except Exception as e:
        logger.exception(f"ERROR: unable to reproject raster: {e}")
        sys.exit(1)
    return out_raster


def select_pixel(prob, transform):
    """
    Select a random pixel from a raster
    :params prob: the probability for selection of a cell
    :param transform: rasterio.transform.Affine of the raster associated with prob
    :return:
    """
    cell_index = np.arange(0, prob.size, 1)
    selected_index = np.random.choice(a=cell_index, size=1, p=prob.ravel())
    cell_index = cell_index.reshape(prob.shape)
    return numpy2coords(cell_index, selected_index, transform)


def numpy2coords(cell_index, selected_index, transform):
    """
    Return the geogr. coordinates of a numpy cell
    :param arr: ndarray representing the raster
    :param value: the index value
    :param transform: rasterio.transform of the raster
    :return:
    """
    row, col = np.where(cell_index == selected_index)
    coords = rio.transform.xy(transform=transform, rows=row, cols=col, offset="center")
    if isinstance(coords[0], list):
        coords = (coords[0][0], coords[1][0])
    return coords


def generate_routes(
    aoi,
    n_trips,
    pop_file,
    poi_type_list,
    poi_dir,
    profile,
    ors_url,
    time_of_day_dict,
    max_distance,
    min_distance,
    default_ors_request,
    testenv,
    data_dir,
    out_dir_dict,
    sensitivity_factor,
):
    """
    Generates random routes. Start point is randomly chosen based on population density. End points are chosen depending
    on distribution of POIs.
    :param n_trips: number of routes to be requested
    :param pop_file: Path to file containing population data (raster)
    :param poi_file: Path to file containing pois (vector)
    :param aoi: GeoDataFrame with aoi
    :param data_dir: root path to data folder
    :param out_dir: root path to export folder
    :param profile: type of movement
    :param ors_url: URL to HEAL-ORS server
    :param time_of_day_dict: dictionary containing columns (times of day) of shadow data with according output values
    :param default_ors_request: default request
    :return: GeoDataFrame containing the generated routes
    """

    logger = logging.getLogger(__file__)

    if testenv is True:
        np.random.seed(10)

    start_point_generator = StartPointGenerator(logger, data_dir, pop_file, aoi)
    start_point = next(start_point_generator)

    generated_routes = []
    default_routes_sol_data = []
    default_segments_sol_data = []
    route_i = 0

    heal_ors_request = copy.deepcopy(default_ors_request)
    heal_ors_request["options"]["profile_params"]["weightings"]["csv_factor"] = sensitivity_factor

    ors_client = RoutingClient(base_url=ors_url)

    for poi_type in poi_type_list:
        item = poi_dir / f"{poi_type}.geojson"
        generated_i = 0

        logger.info(f"Generating routes for {poi_type}...")

        with open(item, encoding="utf-8") as poi_data:
            poi_df = gpd.read_file(poi_data).to_crs("epsg:32632")  # hardcode for meters

            while generated_i < n_trips:
                start_point = next(start_point_generator)
                start_point_utm = reproject_geometry(start_point, "epsg:4326", "epsg:32632")  # hardcode

                nearby_pois = search_nearby_pois(max_distance, min_distance, start_point_utm, poi_df)
                if nearby_pois.empty:
                    continue  # skip loop, choose new start point

                destination_point = nearby_pois.sample().geometry.values[0]
                destination_point = reproject_geometry(destination_point, "epsg:32632", "epsg:4326")  # hardcode

                # calculate route
                try:
                    time_of_day_0 = list(time_of_day_dict.keys())[0]
                    default_ors_request["options"]["profile_params"]["weightings"][
                        "csv_column"
                    ] = time_of_day_0  # reset to first time of day shadow data
                    default_ors_request["coordinates"] = list(start_point.coords) + list(
                        destination_point.coords
                    )
                    default_response = ors_client.request(
                        params=default_ors_request, profile=profile, format="geojson"
                    )
                    default_route = default_response.routes[0]
                    if int(default_route.distance) > max_distance:
                        continue
                    else:
                        route_i += 1

                    default_routes_sol_data.append(
                        {
                            "route_i": route_i,
                            time_of_day_dict[time_of_day_0]: default_route.solar_exposure.tolist(),
                        }
                    )
                    default_segments_sol_data.append(
                        {
                            "route_i": route_i,
                            time_of_day_dict[time_of_day_0]: default_route.values("csv").tolist(),
                        }
                    )

                    # request shadow data for the other times of day for same default route geometry
                    for time_of_day in list(time_of_day_dict.keys())[1:]:
                        default_ors_request["options"]["profile_params"]["weightings"][
                            "csv_column"
                        ] = time_of_day
                        default_response = ors_client.request(
                            params=default_ors_request, profile=profile, format="geojson"
                        )
                        default_route = default_response.routes[0]
                        default_routes_sol_data[route_i - 1][
                            time_of_day_dict[time_of_day]
                        ] = default_route.solar_exposure.tolist()
                        default_segments_sol_data[route_i - 1][
                            time_of_day_dict[time_of_day]
                        ] = default_route.values("csv").tolist()

                    out_folder = utils.subfolder(out_dir_dict["data_routes"], default_ors_request["preference"])
                    out_file_default = (
                        out_folder / f"routes_{default_ors_request['preference']}_{route_i}_{poi_type}.geojson"
                    )
                    default_route.to_file(out_file_default)

                    generated_routes.append(default_route)  # count the routes to check if under n_trips

                    heal_ors_request["coordinates"] = list(start_point.coords) + list(destination_point.coords)
                    for time_of_day in list(time_of_day_dict.keys()):  # create Route for every time of day
                        heal_ors_request["options"]["profile_params"]["weightings"]["csv_column"] = time_of_day
                        heal_response = ors_client.request(
                            params=heal_ors_request, profile=profile, format="geojson"
                        )
                        heal_route = heal_response.routes[0]
                        out_folder = utils.subfolder(out_dir_dict["data_routes"], time_of_day_dict[time_of_day])
                        out_file_heal = out_folder / f"routes_heal_{route_i}_{poi_type}.geojson"
                        heal_route.to_file(out_file_heal)

                except TimeoutError as e:
                    logger.exception(e)
                    break
                except ValueError as e:
                    logger.exception(e)
                    with open("./error_log.txt", "a") as f:
                        f.write("\n\n")
                        json.dump(default_ors_request, f, indent=4)
                        f.write(f"\nError message: {e}")
                        f.write("\n\n---------------------\n---------------------")
                    continue
                except requests.exceptions.ConnectionError:
                    logger.exception(
                        f"Connection error: {ors_url} is not available. Check your connection or the ORS url config parameter."
                    )
                    sys.exit(0)
                except Exception:
                    logger.exception("Error during ORS request: ")
                    continue

                generated_i += 1

    with open(
        out_dir_dict["exportdata"] / f"{default_ors_request['preference']}_routes_sol_data.json", "w"
    ) as f:
        json.dump(default_routes_sol_data, f, indent=4)
    with open(
        out_dir_dict["exportdata"] / f"{default_ors_request['preference']}_segments_sol_data.json", "w"
    ) as f:
        json.dump(default_segments_sol_data, f, indent=4)
