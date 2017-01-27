from shapely import geometry
import geojson
from grid import Grids
def json2polygon(geojson_str):
    """
    convert geojson from data return to polygon
    :param geojson:
    :return: polygon
    """
    geojson_object = geojson.loads(geojson_str)
    return geometry.shape(geojson_object)
field_json = '{"type":"Polygon","coordinates":[[[-100.31238555908205,41.76961530342357],[-100.31496047973634,41.76772683171351],[-100.31543254852296,41.76481399516627],[-100.31405925750734,41.762445217401876],[-100.31169891357423,41.761612923372795],[-100.30835151672365,41.76132481907832],[-100.30577659606934,41.762445217401876],[-100.30427455902101,41.76417379358331],[-100.30380249023439,41.76622241616344],[-100.30500411987306,41.768270973331255],[-100.30689239501953,41.76948727319993],[-100.30946731567384,41.77003139988574],[-100.31238555908205,41.76961530342357]]]}'

field = json2polygon(field_json)
grid_gen = Grids(field)
grids = grid_gen.grids

print len(grids)