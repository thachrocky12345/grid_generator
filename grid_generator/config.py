from etl.pgdb import PgsqlExecutor


test_db = dict(
    host='tp',
    database='wre_fn',
    user='thachbui',
    password='thach12345',
    port='5432'

)

db = PgsqlExecutor(test_db)