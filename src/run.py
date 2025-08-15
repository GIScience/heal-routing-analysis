#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analysis of shade-optimized routing using OpenRouteService"""


import argparse
import geopandas as gpd
import osmnx as ox
import sys
from pathlib import Path
from alive_progress import alive_bar

from modules.utils import load_config, init_logger
from modules.validate_config import validate_config
from modules.cleanup import full_cleanup, cleanup_temp
from modules.download_pois import load_osm_tags, download_features
from modules.route_generator import generate_routes
from modules.evaluation import evaluate_routes


def main(config_file, ors_config_file, developer_config_file):
    """Main function for route analysis"""

    logger = init_logger("route_analysis")

    logger.info("Validating config parameters...")
    config, ors_config, developer_config = load_config(config_file, ors_config_file, developer_config_file)
    config, ors_config, developer_config = validate_config(config, ors_config, developer_config)

    # Developer config file params
    data_dir = developer_config.data_dir
    out_dir = developer_config.out_dir
    poi_dir = developer_config.poi_dir
    poi_tags_file = developer_config.poi_tags_file
    time_of_day_dict = developer_config.time_of_day_dict
    optimized_type = developer_config.optimized_type
    testenv = developer_config.testenv
    response_cache = developer_config.response_cache

    # Config file params
    aoi_name = config.aoi_name
    sensitivity_factor = config.sensitivity_factor
    day = config.day
    n_routes = config.n_routes
    max_distance = config.max_distance
    min_distance = config.min_distance
    solar_threshold_dict = config.solar_threshold_dict
    pop_file = data_dir / config.pop_file
    poi_type_list = config.poi_type_list
    osm_timestamp = config.osm_timestamp

    # ORS config file params
    ors_url = ors_config.ors_url
    profile = ors_config.profile
    default_ors_request = ors_config.default_ors_request

    with alive_bar(7, stats=False, calibrate=70) as bar:
        # cleanup
        logger.info("Cleaning up...")
        out_dir = out_dir / f"{day}" / f"{sensitivity_factor}"
        if out_dir.exists():
            full_cleanup(data_dir, out_dir)
        else:
            logger.info("Cleanup not necessary.")
        bar()

        # out folder structure
        logger.info("Creating results folder structure...")
        try:
            outdata = out_dir / "exportdata"
            outdata_routes = outdata / "routes"
            outdata_segments = outdata / "segments"
            outdata_aggregation = outdata / "aggregation"

            out_dir_dict = {
                "out_dir": outdata,
                "exportdata": outdata,
                "data_routes": outdata_routes,
                "data_segments": outdata_segments,
                "aggregation": outdata_aggregation,
            }
            for dir in out_dir_dict.values():
                dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.exception(f"Error during folder creation: {e}")
            sys.exit(1)
        bar()

        # get aoi boundaries
        logger.info("Getting aoi boundaries...")
        aoi_path = data_dir / aoi_name
        if Path(aoi_path).exists():
            aoi_bpoly = gpd.read_file(aoi_path).to_crs(epsg=4326)
        else:
            logger.info("Aoi file not found. Trying to query it...")
            try:
                aoi_bpoly = ox.geocode_to_gdf(aoi_name).to_crs(epsg=4326)
            except Exception as e:
                logger.exception(f"Error when quering the aoi: {e}")
                sys.exit(1)
        bar()

        # download pois
        try:
            logger.info("Downloading pois...")
            poi_dir = data_dir / poi_dir
            poi_tags_file = data_dir / poi_tags_file
            poi_tags = load_osm_tags(poi_tags_file)
            poi_dir.mkdir(exist_ok=True)

            poi_type_list = download_features(
                poi_tags=poi_tags,
                poi_type_list=poi_type_list,
                bpolys_file=aoi_bpoly,
                timestamp=osm_timestamp,
                properties="tags,metadata",
                outdir=poi_dir,
                overwrite=False,
            )
        except Exception as e:
            logger.exception(f"Error during poi download: {e}")
            sys.exit(1)
        bar()

        # route generation
        n_trips = round(n_routes / len(poi_type_list))
        logger.info(f"Generating {n_trips} trips for each poi type...")
        try:
            generate_routes(
                aoi_bpoly,
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
            )
        except Exception as e:
            logger.exception(f"Error during simulation of routes: {e}")
            sys.exit(1)
        bar()

        # route evaluation
        try:
            logger.info("Evaluating routes...")
            route_level_filename = "route_level_statistics"
            segment_level_filename = "segment_level_statistics"
            evaluate_routes(
                n_trips,
                solar_threshold_dict,
                poi_type_list,
                time_of_day_dict,
                default_ors_request["preference"],
                optimized_type,
                out_dir_dict,
                route_level_filename,
                segment_level_filename,
                response_cache,
                bar,
            )
        except Exception as e:
            logger.exception(f"Error during evaluation of routes: {e}")
            sys.exit(1)
        bar()

        # cleanup
        logger.info("Cleaning up...")
        cleanup_temp(data_dir)
        bar()

        logger.info("Finished.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="HEAL routing analysis")
    required_args = parser.add_argument_group("required arguments")
    optional_args = parser.add_argument_group("optional arguments")
    required_args.add_argument(
        "-c",
        "--config",
        required=True,
        dest="config_file",
        type=str,
        metavar="\b",
        help="Filepath | Configuration file. Example: config/config_sample.yaml",
    )
    optional_args.add_argument(
        "-oc",
        "--ors_config",
        dest="ors_config_file",
        type=str,
        metavar="\b",
        help="Filepath | ORS configuration file. Default: config/conf/ors_config.yaml",
        default="config/conf/ors_config.yaml",
    )
    optional_args.add_argument(
        "-dc",
        "--developer_config",
        dest="developer_config_file",
        type=str,
        metavar="\b",
        help="Filepath | Developer configuration file. Default: config/conf/developer_config.yaml",
        default="config/conf/developer_config.yaml",
    )

    args = parser.parse_args()

    main(Path(args.config_file), Path(args.ors_config_file), Path(args.developer_config_file))
