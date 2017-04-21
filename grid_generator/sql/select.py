get_field_based_on_80per_overlapped = '''

WITH

  Field AS (SELECT st_setsrid(st_geomfromtext(%(polygon_wkt)s), 4326) AS field_boundary_insert)

SELECT

      fb.id, fb.account_device_id, st_asgeojson(fb.geom) AS field_json

FROM
      test_ist.field_boundary fb, Field

WHERE
      st_intersects(fb.geom, Field.field_boundary_insert)

      AND
      (
        (st_area(st_intersection(fb.geom, Field.field_boundary_insert))/st_area(fb.geom)) > 0.85
          OR
        (st_area(st_intersection(Field.field_boundary_insert, fb.geom))/st_area(Field.field_boundary_insert)) >  0.85
      )


'''


get_grids_by_angle = '''
WITH

  Field AS (SELECT st_setsrid(st_geomfromtext(%(polygon_wkt)s), 4326) AS field_boundary_insert)

select * from test_ist.field_grid, Field f where ST_Intersects(f.field_boundary_insert, geom)

'''