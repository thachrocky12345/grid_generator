from shapely.geometry import Polygon
from shapely import geometry
import geojson
from shapely import geometry
import pyproj as pj
import functools as ft
from shapely.ops import cascaded_union, transform

import uom
import math


def json2polygon(geojson_str):
    """
    convert geojson from data return to polygon
    :param geojson:
    :return: polygon
    """
    geojson_object = geojson.loads(geojson_str)
    return geometry.shape(geojson_object)


def get_bbox(polygon):
    min_long, min_lat, max_long, max_lat = polygon.bounds
    return Polygon([(min_long, max_lat),
                    (max_long, max_lat),
                    (max_long, min_lat),
                    (min_long, min_lat)])


def calculate_radius(polygon):
    """
        calculate radius of field circle polygon
        :param polygon: shapely.geometry.Polygon
        :return: uom object
    """
    radius = math.sqrt(calculate_areas(polygon).value / math.pi)
    return uom.Uom(radius, uom.Meter)


def calculate_areas(polygon):
    """
    calculate area of polygon
    :param polygon: shapely.geometry.Polygon
    :return: uom object
    """
    project = ft.partial(pj.transform,
                         pj.Proj(init='epsg:4326'),
                         pj.Proj('+proj=eck4 +lat_0=' + str(polygon.centroid.y) + ' +lon_0=' + str(polygon.centroid.x)))
    field_projected = transform(project, polygon)
    # convert from square meters to acres
    return uom.Uom(field_projected.area, uom.SquareMeter)