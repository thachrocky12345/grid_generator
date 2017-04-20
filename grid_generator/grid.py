
import pyproj
from shapely import ops, geometry

DISTANCE_5_METERS = 5

DEGREE_LONG_DISTANCE = 5.90079939826e-05
DEDREE_LAT_DISTANCE = 4.48390108758e-05


from base import Dto, DtoInteger, DtoObject, DtoUom, DtoNumeric
import uom


class DtoFieldGrid(Dto):
    def __init__(self, **kwargs):
        Dto.__init__(self)
        self.add_attr('id', DtoInteger(), read_only=True)
        self.add_attr('field_boundary_id', DtoInteger(), nullable=False, has_default=False)
        self.add_attr('geometry', DtoObject())
        self.add_attr('field_management_zone_id', DtoInteger(), nullable=False, has_default=False)
        self.add_attr('field_zone_id', DtoInteger(), nullable=False, has_default=False)
        self.add_attr('depletion', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('accumulated_depletion', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('crop_et_stress', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('accumulated_crop_et_stress', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('available_water', DtoUom(uom.NoUom), nullable=False, has_default=True)
        self.add_attr('potential_yield_loss', DtoUom(uom.NoUom), nullable=False, has_default=True)
        self.add_attr('irrigation', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('srid', DtoInteger(), value=4326, read_only=True)
        self.add_attr('irrigation_start_degree', DtoInteger(), read_only=True)
        self.add_attr('irrigation_vri_application_point_id', DtoInteger(), read_only=True)
        self.update(**kwargs)



class Grid(object):
    def __init__(self, longitude, latitude, longitude_distance=DEGREE_LONG_DISTANCE, latitude_distance=DEDREE_LAT_DISTANCE):
        self.long = longitude
        self.lat = latitude
        self.longitude_distance = longitude_distance
        self.latitude_distance = latitude_distance

    @property
    def point_sql(self):
        return '''st_setsrid(st_point({long}, {lat}), 4326)'''.format(long=self.long, lat=self.lat)

    @property
    def point(self):
        return geometry.Point(self.long, self.lat)

    @property
    def polygon_sql(self):
        input = dict(min_long=self.long,
                     max_long=self.long + self.longitude_distance,
                     min_lat=self.lat,
                     max_lat=self.lat - self.latitude_distance)
        return '''st_setsrid('POLYGON(({min_long} {max_lat},{max_long} {max_lat},{max_long} {min_lat},{min_long} {min_lat},{min_long} {max_lat}))'::geometry, 4326)'''.format(**input)

    @property
    def polygon(self):
        min_long = self.long
        max_long = self.long + self.longitude_distance
        min_lat = self.lat
        max_lat = self.lat - self.latitude_distance

        return geometry.Polygon([[min_long, max_lat],
                                 [max_long, max_lat],
                                 [max_long, min_lat],
                                 [min_long, min_lat],
                                 [min_long, max_lat]])

class Grids(object):
    _grids = None
    _lon_distance = None
    _lat_distance = None

    def __init__(self, min_long, min_lat, max_long, max_lat):

        self.min_long = min_long
        self.min_lat = min_lat
        self.max_long = max_long
        self.max_lat = max_lat

    def _set_bbox_(self, polygon):
        bbox = polygon.bounds
        self.min_long = bbox[0]
        self.min_lat = bbox[1]
        self.max_long = bbox[2]
        self.max_lat = bbox[3]

    @property
    def grids(self):
        if self._grids is not None:
            return self._grids

        self._grids = self._get_grids()
        return self._grids


    @property
    def my_proj(self):
        return pyproj.Proj("+proj=eck4 +lat_0={lat} +lon_0={long}, init='epsg:4326".format(
            lat=(self.min_lat + self.max_lat) / 2,
            long=(self.min_long + self.max_long) / 2))

    @property
    def longitude_distance(self):
        if self._lon_distance is not None:
            return self._lon_distance
        begin_point = geometry.Point(self.min_long, self.max_lat)

        UTMx, UTMy = self.my_proj(begin_point.x, begin_point.y, inverse=False)

        long_plus_5m, _ = self.my_proj(UTMx + DISTANCE_5_METERS, UTMy, inverse=True)

        self._lon_distance = abs(self.min_long - long_plus_5m)
        return self._lon_distance


    @property
    def latitude_distance(self):
        if self._lat_distance is not None:
            return self._lat_distance
        begin_point = geometry.Point(self.min_long, self.max_lat)

        UTMx, UTMy = self.my_proj(begin_point.x, begin_point.y, inverse=False)

        _, lat_plus_5m = self.my_proj(UTMx, UTMy + DISTANCE_5_METERS, inverse=True)

        self._lat_distance = abs(self.max_lat - lat_plus_5m)
        return self._lat_distance

    def _get_grids(self):
        """
        Collect all the points
        :param long: from left to right
        :param lat: from up to down
        :param points:
        :return: list of all point sql ready to insert example st_setsrid(
            'POLYGON((min_long max_lat,max_long max_lat,max_long min_lat,min_long min_lat,min_long max_lat))'::geometry
                              , 4326)
        """
        grids = []
        long = self.min_long
        lat = self.max_lat
        while lat >= self.min_lat:
            while long <= self.max_long:
                grids.append(Grid(long, lat, self.longitude_distance, self.latitude_distance))
                long += self.longitude_distance
            long = self.min_long
            lat -= self.latitude_distance

        return grids


