import sys
sys.path.append("/home/thachbui/workstation/grid_generator/grid_generator")
from base import Dto, DtoInteger, DtoObject, DtoUom, DtoNumeric
import uom


class DtoFieldGrid(Dto):
    def __init__(self, **kwargs):
        Dto.__init__(self)
        self.add_attr('id', DtoInteger(), read_only=True)
        self.add_attr('account_device_id', DtoInteger(), nullable=False, has_default=False)
        self.add_attr('geometry', DtoObject())
        self.add_attr('field_management_zone_id', DtoInteger(), nullable=False, has_default=False)
        self.add_attr('field_zone_id', DtoInteger(), nullable=False, has_default=False)
        self.add_attr('depletion', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('accumulated_depletion', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('crop_et_stress', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('accumulated_crop_et_stress', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('available_water', DtoUom(uom.NoUom), nullable=False, has_default=True)
        self.add_attr('potential_yield_loss', DtoUom(uom.NoUom), nullable=False, has_default=True)
        self.add_attr('irrigation', DtoUom(uom.Meter), nullable=False, has_default=True)
        self.add_attr('srid', DtoInteger(), value=4326, read_only=True)
        self.add_attr('irrigation_start_degree', DtoInteger(), read_only=True)
        self.add_attr('irrigation_vri_application_point_id', DtoInteger(), read_only=True)
        self.update(**kwargs)


test = DtoFieldGrid()
# print test

test.account_device_id = 1
test.id = 2
test.geometry = 'geometry'
print test
print test.geometry,  (type(test.geometry))