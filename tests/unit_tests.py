import unittest
import pyproj

from grid_generator import grid


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.longitude = -94.8741
        self.latitude = 39.23625
        self.maxDiff = None

    def test_global_variables(self):
        self.assertEqual(grid.DISTANCE_5_METERS, 5)

    @property
    def Grid(self):
        return grid.Grid(self.longitude, self.latitude)

    def test_grid_point(self):

        self.assertEqual(self.Grid.point_sql(),
                         '''st_setsrid(st_point(-94.8741, 39.23625), 4326)'''
                         )

    def test_grid_polygon(self):
        self.assertEqual(self.Grid.polygon_sql(0.0005, 0.0005),
                         '''st_setsrid('POLYGON((-94.8741 39.23575,-94.8736 39.23575,-94.8736 39.23625,-94.8741 39.23625,-94.8741 39.23575))'::geometry, 4326)''')

    @property
    def Grids(self):
        return grid.Grids(min_long=self.longitude,
                          min_lat=self.latitude,
                          max_long=self.longitude + 0.1,
                          max_lat=self.latitude + 0.1)

    def test_longitude_latitude_distance(self):
        self.assertEqual(self.Grids.longitude_distance, 5.7986717024505197e-05)
        self.assertEqual(self.Grids.latitude_distance, 4.503002124778277e-05)