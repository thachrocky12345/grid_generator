clean_grids = '''

DELETE FROM test_ist.field_grid
WHERE
  field_boundary_id = %(field_id)s
'''