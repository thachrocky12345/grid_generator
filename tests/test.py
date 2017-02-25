import geojson

import functools
import pyproj
from shapely import ops, geometry

from grid_generator.grid import Grids

METERS_TO_ACRES = 0.000247105


def calculate_acres(polygon):
    """
    This function is used to calculate acres from a polygon object, using its
    centroid as projection's point
    :param polygon:
    :return: area in acres unit
    """
    project = functools.partial(pyproj.transform,
                                pyproj.Proj(init='epsg:4326'),
                                pyproj.Proj('+proj=eck4 +lat_0=' + str(polygon.centroid.y) +
                                            ' +lon_0=' +
                                            str(polygon.centroid.x)))
    field_projected = ops.transform(project, polygon)
    # convert from square meters to acres
    ret_acres = field_projected.area

    return ret_acres

def json2polygon(geojson_str):
    """
    convert geojson from data return to polygon
    :param geojson:
    :return: polygon
    """
    geojson_object = geojson.loads(geojson_str)
    return geometry.shape(geojson_object)
field_json = '{"type":"Polygon","coordinates":[[[-100.31238555908205,41.76961530342357],[-100.31543254852296,41.76481399516627],[-100.30577659606934,41.762445217401876],[-100.30500411987306,41.768270973331255],[-100.31238555908205,41.76961530342357]]]}'


field = json2polygon(field_json)
print "meters square: {}".format(calculate_acres(field))
print "expect number of grids: {}".format(calculate_acres(field) / 25)
print field.bounds


grid_gen = Grids(*field.bounds)

print grid_gen.longitude_distance, grid_gen.latitude_distance
grids = grid_gen.grids


print len(grids)