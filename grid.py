import sys
sys.path.append("/home/thachbui/workstation/elecsys_database")

from database import PgPass, PgsqlExecutor


LONGITUDE_DISTANCE = 0.00006
LATITUDE_DISTANCE = 0.000045


class Grid(object):
    def __init__(self, longitude, latitude):
        self.long = longitude
        self.lat = latitude

    @property
    def point_sql(self):
        return '''st_setsrid(
                            st_point({long}, {lat})
                            , 4326)'''.format(long=self.long, lat=self.lat)

    @property
    def polygon_sql(self):
        input = dict(min_long=self.long - LONGITUDE_DISTANCE/2,
                     max_long=self.long + LONGITUDE_DISTANCE/2,
                     min_lat=self.lat - LATITUDE_DISTANCE/2,
                     max_lat=self.lat + LATITUDE_DISTANCE/2)
        return '''st_setsrid(
                             'POLYGON(({min_long} {max_lat},{max_long} {max_lat},{max_long} {min_lat},{min_long} {min_lat},{min_long} {max_lat}))'::geometry
                              , 4326)'''.format(**input)


class Grids(object):
    _grids = None

    def __init__(self, polygon):

        self.max_long = None
        self.min_long = None
        self.max_lat = None
        self.min_lat = None

        self.__set_bbox__(polygon)

    def __set_bbox__(self, polygon):
        bbox = polygon.bounds
        self.min_long = bbox[0]
        self.min_lat = bbox[1]
        self.max_long = bbox[2]
        self.max_lat = bbox[3]

    @property
    def grids(self):
        if self._grids is not None:
            return self._grids

        self._grids = self.get_point(self.min_long, self.max_lat)
        return self._grids


    def get_point(self, long, lat, points=None):
        """
        Collect all the points
        :param long: from left to right
        :param lat: from up to down
        :param points:
        :return: list of all grids
        """

        if points == None:
            points = []

        while lat >= self.min_lat   :
            while long <= self.max_long:
                points.append(Grid(long, lat))
                long += LONGITUDE_DISTANCE
            long = self.min_long
            lat -= LATITUDE_DISTANCE

        points.append(Grid(self.max_long, self.max_lat))
        return points


