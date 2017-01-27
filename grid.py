import sys
sys.path.append("/home/thachbui/workstation/elecsys_database")

from database import PgPass, PgsqlExecutor


LONGITUDE_DISTANCE = 0.000006
LATITUDE_DISTANCE = 0.0000045


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

        self._grids = self.get_point(self.min_long, self.min_lat)
        return self._grids


    def get_point(self, long, lat, points=None):
        """
        Collect all the points
        :param long:
        :param lat:
        :param points:
        :return: list of all points
        """

        if points == None:
            points = [[self.min_long, self.min_lat]]

        while long <= self.max_long and lat <= self.max_lat:
            if long <= self.max_long:
                long += LONGITUDE_DISTANCE
                points.append([long, lat])

            if lat <= self.max_lat:
                lat += LATITUDE_DISTANCE
                points.append([long, lat])

        points.append([self.max_long, self.max_lat])
        return points


