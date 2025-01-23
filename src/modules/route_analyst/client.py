#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simulates routes using openrouteservice"""

import openrouteservice as ors

from .response import RoutingResponse


class RoutingClient:
    """Class for the request to ORS client"""

    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initializes parameters and sends request to ORS server
        :param params: dict
        :param base_url: string
        """
        self.base_url = base_url  # if base_url else
        self.api_key = api_key
        self.__headers = {
            "headers": {
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
                "Authorization": "{}".format(api_key),
                "Content-Type": "application/json; charset=utf-8",
            }
        }
        if self.base_url:
            self.client = ors.Client(base_url=self.base_url)
        else:
            self.client = ors.Client(key=self.api_key)

    def request(self, params: dict, profile: str, format: str) -> RoutingResponse:
        """
        Send route request to ORS server

        :param profile: Name of routing profile
        :param format: Output format
        :param params: dict containing request parameters
        :return: dict of ORS response
        """
        try:
            response = self.client.request(
                url="/v2/directions/{}/{}".format(profile, format),
                post_json=params,
                requests_kwargs=self.__headers,
                get_params=[],
            )
            return RoutingResponse(response)
        except ors.exceptions.ApiError as e:
            raise ValueError(str(e))
