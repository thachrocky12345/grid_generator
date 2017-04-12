
insert_field =  '''
/*
This function is inserting field and returning field_id
input: account_device_id and polygon_wkt
 */

INSERT INTO test_ist.field_boundary(account_device_id, geom) values (
    %(account_device_id)s,
    st_setsrid(st_geomfromtext(%(polygon_wkt)s), 4326)
)

RETURNING id

'''

insert_grids = '''

INSERT INTO test_ist.field_grid(field_boundary_id, geom) values {values}

'''