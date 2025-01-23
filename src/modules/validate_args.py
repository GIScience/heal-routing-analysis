#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check given arguments (config file) and manage global variables (env file)"""

import datetime
import sys
from pathlib import Path
from pydantic import BaseSettings, DirectoryPath, Field, AnyHttpUrl, ValidationError, validator


class ConfigVariables(BaseSettings):
    """Assign and validate content of config file to variables"""

    aoi_name: str = Field(..., regex="(.*\.(gpkg|shp|geojson)$)|(.*\.\s[A-Z].*$)|^(?!.*\.)")
    sensitivity_factor: float = Field(..., ge=0.0, le=1.0)
    day: int = Field(..., ge=90, le=180)
    n_trips: int
    max_distance: int = Field(..., ge=100, le=5000)
    min_distance: int = Field(..., ge=0, le=1000)
    solar_threshold_dict: dict[str, int] = Field(..., ge=1, le=99)
    pop_file: str = Field(..., regex=".*\.tif$")
    poi_type_list: list[str] = Field(..., min_items=1)
    osm_timestamp: datetime.date

    @validator("poi_type_list")
    def validate_poi_type_list(cls, value):
        """Check if poi type is valid"""
        full_poi_list = [
            "general",
            "elderly-people",
            "children",
            "schools",
            "kindergartens",
            "other",
            "primary-care",
            "secondary-care",
            "bus",
            "trams_subway",
            "supermarket",
            "small-shops",
            "market",
            "open-space",
            "places",
            "offices_townhall",
        ]
        for item in value:
            if item not in set(full_poi_list):
                raise ValueError(f"Specified poi type '{item}' not available.")
        return value


class DeveloperconfigVariables(BaseSettings):
    """Assign and validate content of developer config file to variables"""

    data_dir: DirectoryPath
    out_dir: Path
    poi_dir: Path
    poi_tags_file: str = Field(..., regex=".*.json$")
    time_of_day_dict: dict[str, str] = Field(..., min_length=1, max_length=4)
    optimized_type: str
    testenv: bool


class ORSconfigVariables(BaseSettings):
    """Assign and validate content of ors config file to variables"""

    ors_url: AnyHttpUrl
    profile: str = Field(..., regex=".*walking$")
    default_ors_request: dict


def validate_arguments(config, ors_config, developer_config):
    """Validate variables in config files using pydantic"""

    try:
        config = ConfigVariables.parse_obj(config)
        ors_config = ORSconfigVariables.parse_obj(ors_config)
        developer_config = DeveloperconfigVariables.parse_obj(developer_config)
    except ValidationError as e:
        print(e)
        sys.exit(1)

    return (config, ors_config, developer_config)
