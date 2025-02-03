#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simulates routes using openrouteservice"""


import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt


class Route(object):
    """Route calculated using openrouteservice"""

    __dataframe = None

    def __init__(self, json_response):
        """
        Initializes route class
        :param json_response:
        """
        self.__json_response = json_response

    @property
    def json_response(self):
        """
        Returns the ORS response as a dictionary
        :return: dict
        """
        return self.__json_response

    @property
    def coordinates(self):
        """
        Returns the coordinates of the route
        :return: list of coordinates
        """
        return self.json_response["geometry"]["coordinates"]

    @property
    def geometry(self):
        """
        Returns the geometry of the route
        :return:
        """
        return LineString(self.coordinates)

    @property
    def summary(self):
        """
        Return the summary information of the route
        :return:
        """
        return self.json_response["properties"]["summary"]

    @property
    def extras(self):
        """
        Returns the extra information of the route
        :return:
        """
        try:
            return self.json_response["properties"]["extras"]
        except Exception:
            return None

    def values(self, criteria):
        """
        Returns the values for a certain criterion
        :param criterion: 'green', 'noise' or 'steepness'
        :return: values of criterion along route
        """
        return np.concatenate([np.repeat(v[2], v[1] - v[0]) for v in self.extras[criteria]["values"]])

    @property
    def solar_exposure(self):
        """
        Returns the overall exposure to solar radiation of the route
        :return: solar exposure/shadow
        """
        summary = self.summary_criterion("csv")
        return sum(summary["value"] * summary["distance"]) / summary["distance"].sum()

    @property
    def steepness_exposure(self):
        """
        Returns the overall exposure to positive and negative steepness of the route
        :return: steepness exposure for negative and positive values
        """
        summary = self.summary_criterion("steepness")
        pos = []
        neg = []
        dist_Neg = []
        dist_Pos = []
        for o in range(len(summary["value"])):
            if summary["value"][o] > 0:
                pos.append(summary["value"][o])
                dist_Pos.append(summary["distance"][o])
            else:
                neg.append(summary["value"][o])
                dist_Neg.append(summary["distance"][o])

        if sum(dist_Neg) != 0:
            res2 = sum(np.array(neg) * np.array(dist_Neg)) / sum(dist_Neg)
        else:
            res2 = np.nan
        if sum(dist_Pos) != 0:
            res1 = sum(np.array(pos) * np.array(dist_Pos)) / sum(dist_Pos)
        else:
            res1 = np.nan
        return [res1, res2]

    @property
    def noise_exposure(self):
        """
        Returns the overall exposure to noise of the route
        :return: noise exposure
        """
        summary = self.summary_criterion("noise")
        return sum(summary["value"] * summary["distance"]) / summary["distance"].sum()

    @property
    def duration(self):
        """
        Returns the overall duration of the route
        :return: Duration
        """
        return self.summary["duration"]

    @property
    def distance(self):
        """
        Returns the overall distance of the route
        :return: Distance
        """
        return self.summary["distance"]

    @property
    def descent(self):
        """
        Returns the overall distance of the route
        :return:
        """
        return self.json_response["properties"]["descent"]

    @property
    def ascent(self):
        """
        Returns the overall distance of the route
        :return:
        """
        return self.json_response["properties"]["ascent"]

    def summary_criterion(self, criterion):
        """
        Returns the summary for a certain criterion of the ORS response as a pandas dataframe
        :param criterion: 'green', 'noise' or 'steepness'
        :return: Dataframe with summary
        """
        if criterion in self.extras.keys():
            return pd.DataFrame(self.extras[criterion]["summary"])
        else:
            raise ValueError("criterion '%s' does not exist.")

    def plot_summary(self, criterion):
        """
        Returns a bar plot of the summary for a certain criterion
        :param criterion: 'green', 'noise' or 'steepness'
        :return: Bar plot showing summary
        """
        summary = self.summary_criterion(criterion)
        return plt.bar(x=summary["value"], height=summary["amount"], color="green")

    @property
    def route_segments(self):
        """
        Returns segments of the route
        :return: list of LineStrings
        """
        n_segments = len(self.coordinates) - 1
        segments = []
        for i in range(0, n_segments):
            segments.append(LineString(self.coordinates[i : i + 2]))
        return segments

    def as_dataframe(self):
        """
        Converts the route and its extra information into a geopandas dataframe
        :return: GeoDataFrame with route information
        """
        if self.__dataframe is not None:
            return self.__dataframe
        else:
            df = gpd.GeoDataFrame({"geometry": self.route_segments}, crs="epsg:4326")
            if self.extras:
                for k in self.extras.keys():
                    df[k] = self.values(k)
        self.__dataframe = df
        return self.__dataframe

    def to_geojson(self, outfile, driver):
        """
        Writes the route to a geojson file
        :param outfile: Path to output file as string
        :return: geojson file
        """
        self.as_dataframe().to_file(outfile, driver=driver)

    def plot(self, *args, **kwargs):
        """
        Plots the route on a map
        :param args:
        :param kwargs:
        :return: plotted route
        """
        return self.as_dataframe().plot(*args, **kwargs)

    def to_file(self, outfile):
        """
        Writes the whole response to file.
        :param outfile:
        :return:
        """
        with open(outfile, "w") as dst:
            json.dump(self.json_response, dst, indent=4)

    # distance
    def length_diff_meter(self, other_route):
        """
        Calculates the absolute length difference between this route and another route object
        :param other route: Object of type Route
        :return: float value in meters
        """
        return self.distance - other_route.distance

    def length_diff_rel(self, other_route):
        """
        Calculates how much relatively longer this route is in comparison to another route object
        :param other route: Object of type Route
        :return: float value in percent
        """
        return (self.distance - other_route.distance) / other_route.distance * 100

    # duration
    def duration_diff_sec(self, other_route):
        """
        Calculates the absolute duration difference between this route and another route object
        :param other route: Object of type Route
        :return: float value in seconds
        """
        return self.duration - other_route.duration

    def duration_diff_rel(self, other_route):
        """
        Calculates how much relatively more time this route takes in comparison to another route object
        :param other route: Object of type Route
        :return: float value in percent
        """
        return (self.duration - other_route.duration) / other_route.duration * 100

    # geometry
    def same_ratio(self, other_route):
        """
        Calculates how much of this route is same in comparison to another route object
        :param other route: Object of type Route
        :return: float value in percent
        """
        same = self.geometry.intersection(other_route.geometry)
        if same.length == 0:
            return 0
        else:
            return (same.length / self.geometry.length) * 100

    def detour_ratio(self, other_route):
        """
        Calculates how much of this route differs from another route object
        :param other route: Object of type Route
        :return: float value in percent
        """
        detour = self.geometry.difference(other_route.geometry)
        return (detour.length / self.geometry.length) * 100

    def avoided_ratio(self, other_route):
        """
        Calculates how much of the other route is avoided by this route
        :param other route: Object of type Route
        :return: float value in percent
        """
        avoided = self.geometry.difference(other_route.geometry)
        return (avoided.length / other_route.geometry.length) * 100

    def geom_difference(self, other_route):
        """
        Intersects the geometry of this route with another Route object and returns the differing part
        :param other_route: Object of type Route
        :return:
        """
        return self.geometry.difference(other_route.geometry)

    def geom_intersection(self, other_route):
        """
        Intersects the geometry of this route with another Route object and returns the intersecting part
        :param other_route: Object of type Route
        :return:
        """
        return self.geometry.intersection(other_route.geometry)
