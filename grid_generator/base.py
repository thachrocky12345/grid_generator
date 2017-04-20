# from twisted.internet import defer
import psycopg2
from datetime import datetime, date, timedelta

import uom

from lib import defext, date_ext, shapely_ext

import shapely.ops
import shapely.geometry
import geojson


class Null(object):
    def __nonzero__(self):
        return False


class DtoAttributeError(Exception):
    pass


class DtoValueError(Exception):
    pass


class DtoError(object):
    def __init__(self):
        self.invalid_attribute = None
        self.null_error = None
        self.type_error = None
        self.method_error = None

    def __repr__(self):
        return '< {0}, {1} >'.format(self.__class__.__name__, self.__dict__)


class DtoType(object):
    pass


class DtoInteger(DtoType):
    def __repr__(self):
        return 'integer'


class DtoNumeric(DtoType):
    def __repr__(self):
        return 'numeric'


class DtoText(DtoType):
    def __repr__(self):
        return 'text'


class DtoBytea(DtoType):
    def __repr__(self):
        return 'binary'


class DtoBoolean(DtoType):
    def __repr__(self):
        return 'boolean'


class DtoTimestamp(DtoType):
    def __repr__(self):
        return 'timestamp'


class DtoDate(DtoType):
    def __repr__(self):
        return 'date'


class DtoTimeDelta(DtoType):
    def __repr__(self):
        return 'time interval'


class DtoUom(DtoType):
    def __init__(self, base_uom):
        self.base_uom = base_uom

    def __repr__(self):
        return 'Uom'


class DtoObject(DtoType):
    def __repr__(self):
        return 'object'


class Dto(object):
    def __init__(self, **kwargs):
        self._attr_type = {}
        self._nullable = {}
        self._has_default = {}
        self._default_value = {}
        self._read_only = {}
        self.attributes = []

    def __iter__(self):
        for attr in self.attributes:
            if attr not in self.__dict__:
                continue
            yield attr, self.__dict__[attr]

    def iter(self, include_read_only=True, include_none=False):
        for attr, value in self:
            if not include_read_only and self._read_only[attr]:
                continue
            if not include_none and value is None:
                continue
            yield attr, value

    def __nonzero__(self):
        for attr, value in self:
            if value != self._default_value[attr]:
                return True
        return False

    def get_attr(self, attr_name):
        return self.__dict__[attr_name]

    def add_attr(self, attr_name, attr_type=None, nullable=True, has_default=False, value=None, read_only=False):
        if attr_name in self.attributes:
            return
        self.attributes.append(attr_name)
        if isinstance(attr_type, DtoUom) and not isinstance(value, uom.Uom) and value is not None:
            value = uom.Uom(value, attr_type.base_uom)
        self.__dict__[attr_name] = value
        self._default_value[attr_name] = value
        self._attr_type[attr_name] = attr_type
        self._nullable[attr_name] = nullable
        self._has_default[attr_name] = has_default
        self._read_only[attr_name] = read_only

    def rename_attr(self, old_attr, new_attr):
        self.attributes.append(new_attr)
        self.__dict__[new_attr] = self.__dict__[old_attr]
        self._attr_type[new_attr] = self._attr_type[old_attr]
        self._nullable[new_attr] = self._nullable[old_attr]
        self._has_default[new_attr] = self._has_default[old_attr]
        self._read_only[new_attr] = self._read_only[old_attr]
        self.del_attr(old_attr)

    def del_attr(self, attr_name):
        del self.__dict__[attr_name]
        del self._attr_type[attr_name]
        del self._nullable[attr_name]
        del self._has_default[attr_name]
        del self._read_only[attr_name]
        self.attributes.remove(attr_name)

    def properties(self):
        prop = {}
        for attr in self.attributes:
            prop[attr] = {}
            try:
                prop[attr]['type'] = self._attr_type[attr]
            except:
                prop[attr]['type'] = None
            try:
                if isinstance(self._attr_type[attr], DtoUom):
                    prop[attr]['unit'] = self._attr_type[attr].base_uom
            except:
                pass
            try:
                prop[attr]['nullable'] = self._nullable[attr]
            except:
                prop[attr]['nullable'] = None
            try:
                prop[attr]['has_default'] = self._has_default[attr]
            except:
                prop[attr]['has_default'] = None
            try:
                prop[attr]['read_only'] = self._read_only[attr]
            except:
                prop[attr]['read_only'] = None
        return prop

    def convert_type(self, attr, value):
        try:
            if value is None or isinstance(value, Null):
                return value
            if isinstance(self._attr_type[attr], DtoUom) and not isinstance(value, uom.Uom):
                return uom.Uom(value, self._attr_type[attr].base_uom)
            if isinstance(self._attr_type[attr], DtoInteger):
                return int(value)
            if isinstance(self._attr_type[attr], DtoNumeric):
                return float(value)
            if isinstance(self._attr_type[attr], DtoText):
                if not isinstance(value, unicode) and not isinstance(value, str):
                    raise DtoValueError()
            if isinstance(self._attr_type[attr], DtoBytea):
                return psycopg2.Binary(value)
            if isinstance(self._attr_type[attr], DtoBoolean):
                return bool(value)
            if isinstance(self._attr_type[attr], DtoTimestamp):
                if not isinstance(value, datetime):
                    raise DtoValueError()
            if isinstance(self._attr_type[attr], DtoDate):
                if not isinstance(value, date):
                    raise DtoValueError()
            if isinstance(self._attr_type[attr], DtoTimeDelta):
                if not isinstance(value, timedelta):
                    raise DtoValueError()
            return value
        except:
            dto_error = DtoError()
            dto_error.type_error = attr
            raise DtoValueError(dto_error)

    def check_null(self, attr, value):
        if isinstance(value, Null) and not self._nullable[attr]:
            dto_error = DtoError()
            dto_error.null_error = attr
            raise DtoValueError(dto_error)

    def check_attr(self, attr, value):
        if attr not in self.attributes:
            dto_error = DtoError()
            dto_error.invalid_attribute = attr
            raise DtoAttributeError(dto_error)

    def check_default(self, attr):
        value = self.__dict__.get(attr)
        if (value is None or isinstance(value, Null)) and not self._nullable[attr] and not self._has_default[attr]:
            dto_error = DtoError()
            dto_error.null_error = attr
            raise DtoValueError(dto_error)

    def update_attr(self, attr, value):
        self.check_attr(attr, value)
        self.__dict__[attr] = self.convert_type(attr, value)

    def update(self, **values):
        for attr in values:
            self.update_attr(attr, values[attr])

    def update_attr_no_check(self, attr, value):
        self.__dict__[attr] = value

    def update_no_check(self, **values):
        for attr in values:
            self.update_attr_no_check(attr, values[attr])

    def clear(self):
        for key in self.attributes:
            self.__dict__[key] = None

    def __repr__(self):
        return '< {0}, {1} >'.format(self.__class__.__name__, dict(self))


class SqlBuilder(object):
    def __init__(self):
        self.insert = {}
        self.select = {}
        self.update = {}
        self.where = {}

    def add_insert(self, column, value, arg=[]):
        self.insert[column] = {}
        self.insert[column]['value'] = value
        self.insert[column]['arg'] = list(arg)

    def add_select(self, column, value=None, arg=[]):
        self.select[column] = {}
        self.select[column]['value'] = value
        self.select[column]['arg'] = list(arg)

    def add_update(self, column, operator='=', replace='%s', arg=[]):
        self.update[column] = {}
        self.update[column]['replace'] = replace
        self.update[column]['operator'] = operator
        self.update[column]['arg'] = list(arg)

    def add_where(self, column, operator='=', replace='%s', arg=[]):
        self.where[column] = self.where.get(column, {})
        self.where[column][operator] = self.where[column].get(operator, {})
        self.where[column][operator]['replace'] = replace
        self.where[column][operator]['arg'] = list(arg)

    def delete_insert(self, column):
        del self.insert[column]

    def delete_select(self, column):
        del self.select[column]

    def delete_update(self, column):
        del self.update[column]

    def delete_where(self, column):
        del self.where[column]

    def convert_args(self, args, raise_error_on_none=True):
        coverted = []
        for arg in args:
            if arg is None:
                raise ValueError()
            if isinstance(arg, Null):
                arg = None
            coverted.append(arg)
        return coverted

    def get_insert(self):
        column_list = []
        value_list = []
        arg_list = []
        for column in self.insert:
            try:
                arg_list = arg_list + self.convert_args(self.insert[column]['arg'])
            except ValueError:
                # do not include none
                continue
            column_list.append(column)
            value_list.append(self.insert[column]['value'])
        column_list = ', '.join(column_list)
        value_list = ', '.join(value_list)
        return column_list, value_list, tuple(arg_list)

    def get_where(self, sep=' AND ', prefix=''):
        where_list = []
        arg_list = []
        for column in self.where:
            for operator in self.where[column]:
                try:
                    args = self.convert_args(self.where[column][operator]['arg'])
                    arg_list = arg_list + args
                except ValueError:
                    # do not include none
                    continue
                where_list.append('{0}{1} {2} {3}'.format(prefix, column, operator, self.where[column][operator]['replace']))
        where_list = sep.join(where_list)
        if not where_list:
            where_list = True
        return where_list, tuple(arg_list)

    def get_update(self, prefix=''):
        update_list = []
        arg_list = []
        for column in self.update:
            try:
                arg_list = arg_list + self.convert_args(self.update[column]['arg'])
            except ValueError:
                # do not include none
                continue
            update_list.append('{0}{1} {2} {3}'.format(prefix, column, self.update[column]['operator'], self.update[column]['replace']))
        update_list = ', '.join(update_list)
        return update_list, tuple(arg_list)

    def get_select(self, prefix=''):
        select_list = []
        arg_list = []
        for column in self.select:
            arg_list = arg_list + self.convert_args(self.select[column]['arg'], raise_error_on_none=False)
            if self.select[column]['value']:
                select_list.append('{0} AS {1}'.format(self.select[column]['value'], column))
            else:
                select_list.append('{0}{1}'.format(prefix, column))
        select_list = ', '.join(select_list)
        return select_list, tuple(arg_list)

#
# class Mapper(object):
#     def __init__(self, db, DtoClass, table_name):
#         self.DtoClass = DtoClass
#         self.db = db
#         self.table_name = table_name
#
#     def get_sql_builder(self, dto):
#         sql_builder = SqlBuilder()
#         for column, value in dto:
#             operator = '='
#             if isinstance(value, list):
#                 value = tuple(value)
#             if isinstance(value, tuple):
#                 operator = 'IN'
#             sql_builder.add_select(column)
#             sql_builder.add_where(column, operator, '%s', (value,))
#             if dto._read_only[column]:
#                 continue
#             sql_builder.add_insert(column, '%s', (value,))
#             sql_builder.add_update(column, operator, '%s', (value,))
#         return sql_builder
#
#     def get_dto(self, **kwargs):
#         return self.DtoClass(**kwargs)
#
#     def get_dtod(self, dict_key='id', **kwargs):
#         multi_val = kwargs[dict_key]
#         del kwargs[dict_key]
#
#         dtod = {}
#         for val in multi_val:
#             dto = self.get_dto(**kwargs)
#             dto.__dict__[dict_key] = val
#             dtod[val] = dto
#         return dtod
#
#     def get_dtol(self, **kwargs):
#         dto = self.get_dto()
#         for column in kwargs:
#             if isinstance(kwargs[column], list) or isinstance(kwargs[column], tuple):
#                 continue
#             dto.update(**{column: kwargs[column]})
#
#         dtol = []
#         for column in kwargs:
#             if isinstance(kwargs[column], list) or isinstance(kwargs[column], tuple):
#                 for value in kwargs[column]:
#                     dto_temp = self.get_dto(**dict(dto))
#                     dto_temp.update(**{column: value})
#                     dtol.append(dto_temp)
#         if not dtol:
#             dtol = [dto]
#         return dtol
#
#     def convert_to_user(self, dto):
#         dto = self.get_dto(**dict(dto))
#         return dto
#
#     @defer.inlineCallbacks
#     def convert_to_user_dtol(self, dtol):
#         dtol = [self.convert_to_user(dto) for dto in dtol]
#         dtol = yield defext.defer_list(dtol)
#         defer.returnValue(dtol)
#
#     @defer.inlineCallbacks
#     def convert_to_user_dtod(self, dtod):
#         dtod = {key: self.convert_to_user(dtod[key]) for key in dtod}
#         for key in dtod:
#             dtod[key] = yield dtod[key]
#         defer.returnValue(dtod)
#
#     @defer.inlineCallbacks
#     def convert_to_db(self, dto):
#         dto = self.get_dto(**dict(dto))
#         for attr, value in dto:
#             yield dto.check_null(attr, value)
#             if isinstance(dto._attr_type[attr], DtoUom) and isinstance(value, uom.Uom):
#                 value = value.convert(dto._attr_type[attr].base_uom)
#                 dto.update_attr_no_check(attr, value)
#             print attr, value
#         defer.returnValue(dto)
#
#     @defer.inlineCallbacks
#     def convert_to_db_dtol(self, dtol):
#         dtol_temp = [self.convert_to_db(dto) for dto in dtol]
#         dtol = []
#         for dto in dtol_temp:
#             dto = yield dto
#             dtol.append(dto)
#         defer.returnValue(dtol)
#
#     @defer.inlineCallbacks
#     def select(self, dto, where_column='id'):
#         dto = yield self.convert_to_db(dto)
#         sql_builder = self.get_sql_builder(dto)
#         select_list, select_arg_list = sql_builder.get_select()
#         sql = """SELECT {0} FROM {1} WHERE {2} IN (%b)""".format(select_list, self.table_name, where_column)
#         sql_args = select_arg_list + (BulkVar(dto.get_attr(where_column), column=where_column),)
#         db_return = yield self.bulk_db.execute_sql_fetchone(sql, *sql_args, read_only=True)
#         dto = self.get_dto()
#         dto.update_no_check(**db_return)
#         dto = yield self.convert_to_user(dto)
#         defer.returnValue(dto)
#
#     @defer.inlineCallbacks
#     def select_dtol(self, dto, where_column='id', order_by=None):
#         if order_by is None:
#             order_by = where_column
#         dto = yield self.convert_to_db(dto)
#         sql_builder = self.get_sql_builder(dto)
#         select_list, select_arg_list = sql_builder.get_select()
#         sql = """SELECT {0} FROM {1} WHERE {2} IN (%b) ORDER BY {3}""".format(select_list, self.table_name, where_column, order_by)
#         sql_args = select_arg_list + (BulkVar(dto.get_attr(where_column), column=where_column),)
#         db_return = yield self.bulk_db.execute_sql_fetchall(sql, *sql_args, read_only=True)
#         dtol = []
#         for row in db_return:
#             dto = self.get_dto()
#             dto.update_no_check(**row)
#             dtol.append(dto)
#         dtol = yield self.convert_to_user_dtol(dtol)
#         defer.returnValue(dtol)
#
#     @defer.inlineCallbacks
#     def select_cache(self, dto, where_column='id'):
#         dto = yield self.convert_to_db(dto)
#         sql_builder = self.get_sql_builder(dto)
#         select_list, select_arg_list = sql_builder.get_select()
#         sql = """SELECT {0} FROM {1} WHERE {2} IN (%b)""".format(select_list, self.table_name, where_column)
#         sql_args = select_arg_list + (BulkVar(dto.get_attr(where_column), column=where_column),)
#         db_return = yield self.bulk_db.cache_sql_fetchone(sql, *sql_args, read_only=True)
#         dto = self.get_dto()
#         dto.update_no_check(**db_return)
#         dto = yield self.convert_to_user(dto)
#         defer.returnValue(dto)
#
#     @defer.inlineCallbacks
#     def upsert(self, dto, where_column='id', **kwargs):
#         dto_update = yield self.update(dto, where_column=where_column)
#         if dto_update:
#             defer.returnValue(dto_update)
#         dto_insert = yield self.insert(dto, **kwargs)
#         defer.returnValue(dto_insert)
#
#     @defer.inlineCallbacks
#     def update(self, dto, where_column='id'):
#         dto = yield self.convert_to_db(dto)
#         sql_builder = self.get_sql_builder(dto)
#         update_list, update_arg_list = sql_builder.get_update()
#         select_list, select_arg_list = sql_builder.get_select()
#         sql = 'UPDATE {0} SET {1} WHERE {2} = %s RETURNING {3}'.format(self.table_name, update_list, where_column, select_list)
#         sql_args = update_arg_list + (dto.get_attr(where_column),) + select_arg_list
#         db_return = yield self.db.execute_sql_fetchone(sql, *sql_args)
#         dto = self.get_dto()
#         dto.update_no_check(**db_return)
#         dto = yield self.convert_to_user(dto)
#         defer.returnValue(dto)
#
#     @defer.inlineCallbacks
#     def insert(self, dto, **kwargs):
#         dto = yield self.convert_to_db(dto)
#         print dto.wind_speed
#         sql_builder = self.get_sql_builder(dto)
#         column_list, value_list, insert_arg_list = sql_builder.get_insert()
#         select_list, select_arg_list = sql_builder.get_select()
#
#         print column_list, value_list, insert_arg_list
#
#         sql = "INSERT INTO {0} ({1}) VALUES %b RETURNING {2}".format(self.table_name, column_list, select_list)
#         sql_args = (BulkList(*insert_arg_list, replace='(' + value_list + ')'),) + select_arg_list
#
#         try:
#             db_return = yield self.bulk_db.execute_sql_fetchone(sql, *sql_args, **kwargs)
#         except psycopg2.IntegrityError:
#             for attr in dto.attributes:
#                 dto.check_default(attr)
#             raise
#         dto = self.get_dto()
#         dto.update_no_check(**db_return)
#         dto = yield self.convert_to_user(dto)
#         defer.returnValue(dto)
#
#     @defer.inlineCallbacks
#     def delete(self, dto, where_column='id'):
#         dto = yield self.convert_to_db(dto)
#         sql_builder = self.get_sql_builder(dto)
#         select_list, select_arg_list = sql_builder.get_select()
#         sql = """DELETE FROM {0} WHERE {1} = %s RETURNING {2}""".format(self.table_name, where_column, select_list)
#         sql_args = (dto.get_attr(where_column),) + select_arg_list
#         db_return = yield self.db.execute_sql_fetchone(sql, *sql_args)
#         dto = self.get_dto()
#         dto.update_no_check(**db_return)
#         dto = yield self.convert_to_user(dto)
#         defer.returnValue(dto)
#
#     def select_history(self, dto, start_date, end_date):
#         raise NotImplementedError()
#
#     def select_children(self, dto, limit, offset):
#         raise NotImplementedError()
#
#     @defer.inlineCallbacks
#     def select_dtod(self, dtod):
#         for key in dtod:
#             dto = dtod[key]
#             dtod[key] = self.select(dto)
#         for key in dtod:
#             dtod[key] = yield dtod[key]
#         defer.returnValue(dtod)
#
#     def dtol_to_dto(self, dtol, include_duplicate=False, include_none=False):
#         dto_final = self.get_dto()
#         for dto in dtol:
#             for attr, value in dto:
#                 if value is None and not include_none:
#                     continue
#                 if dto_final.__dict__[attr] is None:
#                     dto_final.__dict__[attr] = []
#                 if value in dto_final.__dict__[attr] and not include_duplicate:
#                     continue
#                 dto_final.__dict__[attr].append(value)
#         return dto_final
#
#     def intersection_dtol(self, dtol1, dtol2, dto1_attr='geometry', dto2_attr='geometry'):
#         result = []
#         for dto1 in dtol1:
#             for dto2 in dtol2:
#                 polygon1 = dto1.get_attr(dto1_attr)
#                 polygon2 = dto2.get_attr(dto2_attr)
#                 multipolygon = shapely_ext.intersection(polygon1, polygon2)
#                 polygons = shapely_ext.multipolygon_to_polygon(multipolygon)
#                 for polygon in polygons:
#                     result.append([polygon, dto1, dto2])
#         return result
#
#     def difference_dtol(self, dtol1, dtol2, dto1_attr='geometry', dto2_attr='geometry'):
#         result = []
#         for dto1 in dtol1:
#             for dto2 in dtol2:
#                 polygon1 = dto1.get_attr(dto1_attr)
#                 polygon2 = dto2.get_attr(dto2_attr)
#                 multipolygon = shapely_ext.difference(polygon1, polygon2)
#                 polygons = shapely_ext.multipolygon_to_polygon(multipolygon)
#                 for polygon in polygons:
#                     result.append([polygon, dto1])
#         return result
#
#     def symmetric_difference_dtol(self, dtol1, dtol2, dto1_attr='geometry', dto2_attr='geometry'):
#         result = []
#         for dto1 in dtol1:
#             for dto2 in dtol2:
#                 polygon1 = dto1.get_attr(dto1_attr)
#                 polygon2 = dto2.get_attr(dto2_attr)
#                 multipolygon = shapely_ext.symmetric_difference(polygon1, polygon2)
#                 polygons = shapely_ext.multipolygon_to_polygon(multipolygon)
#                 for polygon in polygons:
#                     result.append([polygon, dto1, dto2])
#         return result
#
#     def union_dtol(self, dtol, dto_attr='geometry'):
#         result = []
#         polygons = []
#         for dto in dtol:
#             polygon = dto.get_attr(dto_attr)
#             polygon = shapely.geometry.shape(polygon)
#             polygons.append(polygon)
#         polygons = shapely.ops.cascaded_union(polygons)
#         for polygon in shapely_ext.get_polygons(polygons):
#             polygon = polygon.simplify(0)
#             polygon = shapely.geometry.mapping(polygon)
#             polygon = geojson.loads(geojson.dumps(polygon))
#             result.append(polygon)
#         return result
#
#     def trim(self, dto_boundary, dtol, dto_attr='geometry'):
#         dtol_trim = []
#         for polygon, dto_boundary, dto in self.intersection_dtol([dto_boundary], dtol):
#             dto.update_attr(dto_attr, polygon)
#             dto.geometry = polygon
#             dtol_trim.append(dto)
#         return dtol_trim
#
#
# class MapperSettingOutput(Mapper):
#     def __init__(self, db, bulk_db, DtoClass, mapper_ads, mapper_dado):
#         Mapper.__init__(self, db, bulk_db, DtoClass, '')
#         self.mapper_ads = mapper_ads
#         self.mapper_dado = mapper_dado
#         self.output = {}
#         self.setting = {}
#
#     @defer.inlineCallbacks
#     def select(self, dto):
#         dto = self.get_dto(account_device_id=dto.account_device_id)
#
#         dtod_dado = self.mapper_dado.get_dtod(device_output_id=self.output.keys(), account_device_id=dto.account_device_id)
#         dtod_ads = self.mapper_ads.get_dtod(device_setting_id=self.setting.keys(), account_device_id=dto.account_device_id)
#         dtod_dado = self.mapper_dado.select_dtod(dtod_dado)
#         dtod_ads = self.mapper_ads.select_dtod(dtod_ads)
#         dtod_dado = yield dtod_dado
#         dtod_ads = yield dtod_ads
#
#         for output_id in dtod_dado:
#             dto.update(**{self.output[output_id]: dtod_dado[output_id].cooked})
#
#         for setting_id in dtod_ads:
#             dto.update(**{self.setting[setting_id]: dtod_ads[setting_id].val})
#         dto = yield self.convert_to_user(dto)
#         defer.returnValue(dto)
#
#     @defer.inlineCallbacks
#     def select_history(self, dto, start_date, end_date):
#         temp = []
#         for output_id in self.output:
#             dto = self.mapper_dado.get_dto(device_output_id=output_id, account_device_id=dto.account_device_id)
#             dto_output = self.mapper_dado.select_history(dto, start_date, end_date)
#             temp.append(dto_output)
#         temp = yield defext.defer_list(temp)
#         dtod = {}
#         for dtod_dado in temp:
#             for created in dtod_dado:
#                 if created not in dtod:
#                     dtod[created] = self.get_dto(account_device_id=dto.account_device_id)
#                 attr = self.output[dtod_dado[created].device_output_id]
#                 dtod[created].update_attr(attr, dtod_dado[created].cooked)
#         defer.returnValue(dtod)
#
#     @defer.inlineCallbacks
#     def update(self, dto, updated=None, update_output=False, overwrite_history=False):
#         if not updated:
#             updated = date_ext.now()
#         values = dict(dto)
#         dlist = []
#         for setting_id in self.setting:
#             val = values[self.setting[setting_id]]
#             dto_ads = self.mapper_ads.get_dto(account_device_id=dto.account_device_id, device_setting_id=setting_id, val=val, updated=updated)
#             dlist.append(self.mapper_ads.update(dto_ads))
#
#         if update_output:
#             for output_id in self.output:
#                 val = values[self.output[output_id]]
#                 dto_dado = self.mapper_dado.get_dto(account_device_id=dto.account_device_id, device_output_id=output_id, cooked=val, created=updated)
#                 if overwrite_history:
#                     dlist.append(self.mapper_dado.insert_overwrite_history(dto_dado))
#                 else:
#                     dlist.append(self.mapper_dado.insert(dto_dado))
#         yield defext.defer_list(dlist)
#         defer.returnValue(dto)
