
import pyproj
from shapely import ops, geometry

DISTANCE_5_METERS = 5


class Grid(object):
    def __init__(self, longitude, latitude):
        self.long = longitude
        self.lat = latitude

    def point_sql(self):
        return '''st_setsrid(st_point({long}, {lat}), 4326)'''.format(long=self.long, lat=self.lat)

    def polygon_sql(self, longitude_distance, latitude_distance):
        input = dict(min_long=self.long,
                     max_long=self.long + longitude_distance,
                     min_lat=self.lat,
                     max_lat=self.lat - latitude_distance)
        return '''st_setsrid('POLYGON(({min_long} {max_lat},{max_long} {max_lat},{max_long} {min_lat},{min_long} {min_lat},{min_long} {max_lat}))'::geometry, 4326)'''.format(**input)


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

        self._grids = self.get_grid_polygons
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

    @property
    def get_grid_points(self):
        """
        Collect all the points
        :param long: from left to right
        :param lat: from up to down
        :param points:
        :return: list of all point sql ready to insert example st_setsrid(
                            st_point( -94.87, 39.23)
                            , 4326)
        """
        points = []
        long = self.min_long
        lat = self.max_lat
        while lat >= self.min_lat :
            while long <= self.max_long:
                points.append(Grid(long, lat))
                long += self.longitude_distance
            long = self.min_long
            lat -= self.latitude_distance

        points.append(Grid(self.max_long, self.min_lat).point_sql)
        return points

    @property
    def get_grid_polygons(self):
        """
        Collect all the points
        :param long: from left to right
        :param lat: from up to down
        :param points:
        :return: list of all point sql ready to insert example st_setsrid(
            'POLYGON((min_long max_lat,max_long max_lat,max_long min_lat,min_long min_lat,min_long max_lat))'::geometry
                              , 4326)
        """
        polygons = []
        long = self.min_long
        lat = self.max_lat
        while lat >= self.min_lat:
            while long <= self.max_long:
                polygons.append(Grid(long, lat).polygon_sql(self.longitude_distance, self.latitude_distance))
                long += self.longitude_distance
            long = self.min_long
            lat -= self.latitude_distance

        return polygons


