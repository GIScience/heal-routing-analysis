#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Downloads OSM data using ohsome api"""


import json

import geopandas as gpd
import logging
from pathlib import Path
from ohsome import OhsomeClient


def download_features(
    poi_tags: list,
    poi_type_list: list,
    outdir: Path,
    timestamp: str = None,
    bbox: str = None,
    bpolys_file: str = None,
    bpolys: gpd.GeoDataFrame = None,
    properties=None,
    overwrite=False,
):
    """
    Downloads all OSM pois, specified in the poi_tags file
    :param bbox: Bounding box in geographic coordinates (minx, miny, maxx, maxy)
    :param layers: List of dictionaries containing tags, geoms, types info for ohsome requests
    :param outdir: Path to directory where osm data should be stored
    :param timestamp: Date and time in ISO-format for OSM data download
    :return:
    """
    logger = logging.getLogger(__file__)

    if (bpolys_file is None) and (bbox is None) and (bpolys is None):
        raise ValueError("Either 'bpolys_file', 'bbox' or 'bpolys' must be given. ")
    if bpolys_file is not None:
        bpolys = bpolys_file
    if properties is None:
        properties = []

    # Set up ohsome client
    ohsome_log = outdir / "ohsome_log"
    ohsome_log.mkdir(exist_ok=True)
    client = OhsomeClient(log_dir=ohsome_log)

    for group_name in poi_tags:
        for layer in poi_tags[group_name]:
            if layer["name"] in poi_type_list:
                logger.info(f"Downloading {layer['name']}...")
                outfile = outdir / f"{layer['name']}.geojson"
                if outfile.exists() and overwrite is False:
                    logger.info(f"{outfile} already exists. Download is skipped.")
                    continue
                if "endpoint" not in layer.keys():
                    layer["endpoint"] = "elements/geometry"
                if "filter" in layer.keys():
                    ohsome_filter_str = layer["filter"]

                response = client.post(
                    endpoint=layer["endpoint"],
                    bpolys=bpolys,
                    bboxes=bbox,
                    time=timestamp,
                    filter=ohsome_filter_str,
                    properties=properties,
                )
                response.to_json(str(outfile))
            else:
                continue


def load_osm_tags(poi_file):
    """
    Load osm tags from file
    :param poi_file: path to poi file (str)
    :return:
    """
    with open(poi_file, "r") as src:
        data = json.load(src)
    return data
