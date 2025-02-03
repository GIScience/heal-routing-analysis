#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simulates routes using openrouteservice"""

import json
from pathlib import Path
from .route import Route


class RoutingResponse:
    """Class of the response after requesting the routes"""

    def __init__(self, json_response: dict = None, file: Path = None):
        """
        Initializes parameters and sends request to ORS server
        :param params: dict
        :param base_url: string
        """
        if json_response:
            self.json_response = json_response
        elif file:
            self.json_response = self.load(file)
        self.routes = []
        self._extract_routes()

    def _extract_routes(self):
        """
        Get routes and their alternatives
        :return: List containing maximum 3 Route objects (1 route and 2 or less alternative routes)
        """
        for route_feature in self.json_response["features"]:
            self.routes.append(Route(json_response=route_feature))

    def _extract_metadata(self):
        """
        Parses metadata from raw json response
        :return:
        """
        pass

    def from_file(self, file):
        """
        Loads route from file
        :param file:
        :return:
        """
        with open(file) as src:
            self.json_response = json.load(src)
