import shapely.geometry
import geojson


def get_polygons(shapely_object):
    if isinstance(shapely_object, shapely.geometry.collection.GeometryCollection):
        polygons = []
        for o in shapely_object:
            polygons = polygons + get_polygons(o)
        return polygons
    elif isinstance(shapely_object, shapely.geometry.polygon.Polygon):
        return [shapely_object]
    elif isinstance(shapely_object, shapely.geometry.multipolygon.MultiPolygon):
        return [polygon for polygon in shapely_object]
    return []


def convert_to_multipolygon(shapely_object):
    polygons = get_polygons(shapely_object)
    polygons = [shapely.geometry.polygon.orient(polygon) for polygon in polygons]
    return shapely.geometry.multipolygon.MultiPolygon(polygons)


def intersection(geojson_object1, geojson_object2):
    shapely_object1 = shapely.geometry.shape(geojson_object1)
    shapely_object2 = shapely.geometry.shape(geojson_object2)
    shapely_object3 = shapely_object1.intersection(shapely_object2)
    shapely_object3 = convert_to_multipolygon(shapely_object3)
    geojson_object3 = shapely.geometry.mapping(shapely_object3)
    geojson_object3 = geojson.loads(geojson.dumps(geojson_object3))
    return geojson_object3


def symmetric_difference(geojson_object1, geojson_object2):
    shapely_object1 = shapely.geometry.shape(geojson_object1)
    shapely_object2 = shapely.geometry.shape(geojson_object2)
    shapely_object3 = shapely_object1.symmetric_difference(shapely_object2)
    shapely_object3 = convert_to_multipolygon(shapely_object3)
    geojson_object3 = shapely.geometry.mapping(shapely_object3)
    geojson_object3 = geojson.loads(geojson.dumps(geojson_object3))
    return geojson_object3


def union(geojson_object1, geojson_object2):
    shapely_object1 = shapely.geometry.shape(geojson_object1)
    shapely_object2 = shapely.geometry.shape(geojson_object2)
    shapely_object3 = shapely_object1.union(shapely_object2)
    shapely_object3 = convert_to_multipolygon(shapely_object3)
    geojson_object3 = shapely.geometry.mapping(shapely_object3)
    geojson_object3 = geojson.loads(geojson.dumps(geojson_object3))
    return geojson_object3


def difference(geojson_object1, geojson_object2):
    shapely_object1 = shapely.geometry.shape(geojson_object1)
    shapely_object2 = shapely.geometry.shape(geojson_object2)
    shapely_object3 = shapely_object1.difference(shapely_object2)
    shapely_object3 = convert_to_multipolygon(shapely_object3)
    geojson_object3 = shapely.geometry.mapping(shapely_object3)
    geojson_object3 = geojson.loads(geojson.dumps(geojson_object3))
    return geojson_object3


def multipolygon_to_polygon(geojson_object):
    shapely_object = shapely.geometry.shape(geojson_object)
    polygons = get_polygons(shapely_object)
    polygons = [shapely.geometry.mapping(polygon) for polygon in polygons]
    polygons = [geojson.loads(geojson.dumps(polygon)) for polygon in polygons]
    return polygons


def bounds(geojson_object):
    shapely_object = shapely.geometry.shape(geojson_object)
    return shapely_object.bounds
