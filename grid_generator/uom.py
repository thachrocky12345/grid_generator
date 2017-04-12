from __future__ import division
import numbers
import math


class UomMismatchError(TypeError):
    pass


class BaseUom(object):
    uom_type_numerator = ()
    uom_type_denominator = ()

    def __init__(self, convert_to_base1, convert_from_base1):
        self.convert_to_base1 = convert_to_base1
        self.convert_from_base1 = convert_from_base1

    def __repr__(self):
        return '< {0}, uom: {1} {2} >'.format(self.__class__.__name__, self.uom_type_numerator, self.uom_type_denominator)

    def __str__(self):
        numerator = '*'.join(self.uom_type_numerator)
        denominator = '*'.join(self.uom_type_denominator)
        return '{0} / {1}'.format(numerator, denominator)

    def convert_to_base(self, value):
        if not isinstance(value, numbers.Number):
            return value
        return self.convert_to_base1(value)

    def convert_from_base(self, value):
        if not isinstance(value, numbers.Number):
            return value
        return self.convert_from_base1(value)

    def __pow__(self, exponent):
        if not isinstance(exponent, int):
            raise TypeError()
        if exponent < 0:
            raise ValueError
        uom = self
        for __ in range(exponent - 1):
            uom = uom.__mul__(self)
        return uom

    def __mul__(self, other):
        if not isinstance(other, BaseUom):
            raise TypeError()
        uom = _CombineUom(other.convert_to_base, self.convert_to_base, self.convert_from_base, other.convert_from_base)
        uom.uom_type_numerator = self.uom_type_numerator
        uom.uom_type_denominator = self.uom_type_denominator

        for uom_name in other.uom_type_denominator:
            if uom_name in uom.uom_type_numerator:
                temp = list(uom.uom_type_numerator)
                temp.remove(uom_name)
                uom.uom_type_numerator = tuple(temp)
            else:
                temp = list(uom.uom_type_denominator)
                temp.append(uom_name)
                uom.uom_type_denominator = tuple(temp)

        for uom_name in other.uom_type_numerator:
            if uom_name in uom.uom_type_denominator:
                temp = list(uom.uom_type_denominator)
                temp.remove(uom_name)
                uom.uom_type_denominator = tuple(temp)
            else:
                temp = list(uom.uom_type_numerator)
                temp.append(uom_name)
                uom.uom_type_numerator = tuple(temp)
        return uom

    def __div__(self, other):
        if not isinstance(other, BaseUom):
            raise TypeError()
        uom = _CombineUom(self.convert_to_base, other.convert_from_base, self.convert_from_base, other.convert_to_base)
        uom.uom_type_numerator = self.uom_type_numerator
        uom.uom_type_denominator = self.uom_type_denominator

        for uom_name in other.uom_type_denominator:
            if uom_name in uom.uom_type_denominator:
                temp = list(uom.uom_type_denominator)
                temp.remove(uom_name)
                uom.uom_type_denominator = tuple(temp)
            else:
                temp = list(uom.uom_type_numerator)
                temp.append(uom_name)
                uom.uom_type_numerator = tuple(temp)

        for uom_name in other.uom_type_numerator:
            if uom_name in uom.uom_type_numerator:
                temp = list(uom.uom_type_numerator)
                temp.remove(uom_name)
                uom.uom_type_numerator = tuple(temp)
            else:
                temp = list(uom.uom_type_denominator)
                temp.append(uom_name)
                uom.uom_type_denominator = tuple(temp)
        return uom

    def __truediv__(self, other):
        return self.__div__(other)

    def __eq__(self, other):
        if not isinstance(other, BaseUom):
            return False

        if other.uom_type_numerator == self.uom_type_numerator and other.uom_type_denominator == self.uom_type_denominator:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class _CombineUom(BaseUom):
    def __init__(self, convert_to_base1, convert_to_base2, convert_from_base1, convert_from_base2):
        self.convert_to_base1 = convert_to_base1
        self.convert_to_base2 = convert_to_base2
        self.convert_from_base1 = convert_from_base1
        self.convert_from_base2 = convert_from_base2

    def convert_to_base(self, value):
        if not isinstance(value, numbers.Number):
            return value
        value = self.convert_to_base1(value)
        value = self.convert_to_base2(value)
        return value

    def convert_from_base(self, value):
        if not isinstance(value, numbers.Number):
            return value
        value = self.convert_from_base1(value)
        value = self.convert_from_base2(value)
        return value


class Uom(object):
    def __init__(self, value, uom=BaseUom(lambda value: value, lambda value: value)):
        if isinstance(value, Uom):
            self.uom = value.uom
            self.value = value.value
        else:
            self.uom = uom
            self.value = value
        self.base_value = self.uom.convert_to_base(self.value)

    def convert(self, uom):
        if self.uom != uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, uom))
        return uom.convert_from_base(self.base_value)

    def at(self, value):
        return Uom(value, self.uom)

    def __repr__(self):
        return '< {0}, value: {1}, uom: {2} >'.format(self.__class__.__name__, self.base_value, self.uom)

    def __nonzero__(self):
        if self.base_value is None:
            return False
        return True

    def __eq__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        return other.base_value == self.base_value and other.uom == self.uom

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        return self.base_value < other.base_value

    def __le__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        return self.base_value <= other.base_value

    def __gt__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        return self.base_value > other.base_value

    def __ge__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        return self.base_value >= other.base_value

    def __and__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        total = Uom(self)
        total.base_value = self.base_value & other.base_value
        return total

    def __or__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        total = Uom(self)
        total.base_value = self.base_value | other.base_value
        return total

    def __add__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))
        total = self.base_value + other.base_value
        total = self.uom.convert_from_base(total)
        return Uom(total, self.uom)

    def __sub__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        if self.uom != other.uom:
            raise UomMismatchError('{0}, {1}'.format(self.uom, other.uom))

        total = self.base_value - other.base_value
        total = self.uom.convert_from_base(total)
        return Uom(total, self.uom)

    def __mul__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other)
        total = self.base_value * other.base_value
        uom = self.uom * other.uom
        total = uom.convert_from_base(total)
        return Uom(total, uom)

    def __div__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other)
        total = self.base_value / other.base_value
        uom = self.uom / other.uom
        total = uom.convert_from_base(total)
        return Uom(total, uom)

    def __radd__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        return other + self

    def __rsub__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other, self.uom)
        return other - self

    def __rmul__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other)
        return other * self

    def __rdiv__(self, other):
        if not isinstance(other, Uom):
            other = Uom(other)
        return other / self

    def __pow__(self, exponent):
        if not isinstance(exponent, int):
            raise TypeError()
        if exponent < 0:
            raise ValueError
        uom = self
        for __ in range(exponent - 1):
            uom = uom.__mul__(self)
        return uom

    def __truediv__(self, other):
        return self.__div__(other)


class UomInt(int, Uom):
    def __new__(cls, value, *args, **kwargs):
        if not isinstance(value, numbers.Number):
            value = 0
        return int.__new__(cls, value)

    def __init__(self, value, *args):
        int.__init__(self, value)
        Uom.__init__(self, value, *args)

    def __repr__(self, *args):
        return Uom.__repr__(self, *args)

    def __str__(self, *args):
        return Uom.__str__(self, *args)

    def __nonzero__(self):
        return Uom.__nonzero__(self)

    def __eq__(self, other):
        return Uom.__eq__(self, other)

    def __ne__(self, other):
        return Uom.__ne__(self, other)

    def __lt__(self, other):
        return Uom.__lt__(self, other)

    def __le__(self, other):
        return Uom.__le__(self, other)

    def __gt__(self, other):
        return Uom.__gt__(self, other)

    def __ge__(self, other):
        return Uom.__ge__(self, other)

    def __add__(self, other):
        return Uom.__add__(self, other)

    def __sub__(self, other):
        return Uom.__sub__(self, other)

    def __mul__(self, other):
        return Uom.__mul__(self, other)

    def __div__(self, other):
        return Uom.__div__(self, other)

    def __pow__(self, exponent):
        return Uom.__pow__(self, exponent)

    def __truediv__(self, other):
        return Uom.__truediv__(self, other)


class BaseNoUom(BaseUom):
    def __str__(self):
        return ''


class BaseLength(BaseUom):
    uom_type_numerator = ('length',)

    def __str__(self):
        return 'Meter'


class BaseArea(BaseUom):
    uom_type_numerator = ('length', 'length')

    def __str__(self):
        return 'Square_Meter'


class BaseTime(BaseUom):
    uom_type_numerator = ('time',)

    def __str__(self):
        return 'Second'


class BaseTemperature(BaseUom):
    uom_type_numerator = ('temperature',)

    def __str__(self):
        return 'Kelvin'


class BaseTemperatureDifference(BaseUom):
    uom_type_numerator = ('temperature_diff',)


class BaseMass(BaseUom):
    uom_type_numerator = ('mass',)

    def __str__(self):
        return 'KiloGram'


class BaseCurrent(BaseUom):
    uom_type_numerator = ('current',)

    def __str__(self):
        return 'Ampere'


class BaseAngle(BaseUom):
    uom_type_numerator = ('angle',)

    def __str__(self):
        return 'Radian'


class BaseFrequency(BaseUom):
    uom_type_denominator = ('time',)

    def __str__(self):
        return 'Hertz'


class BaseVolt(BaseUom):
    uom_type_numerator = ('mass', 'length', 'length')
    uom_type_denominator = ('time', 'time', 'time', 'current')

    def __str__(self):
        return 'Volt'


class BasePressure(BaseUom):
    uom_type_numerator = ('mass',)
    uom_type_denominator = ('length', 'time', 'time')

    def __str__(self):
        return 'Pascal'


class BaseVolume(BaseUom):
    uom_type_numerator = ('length', 'length', 'length')

    def __str__(self):
        return 'Cubic_Meter'


class BaseFlow(BaseUom):
    uom_type_numerator = ('length', 'length', 'length')
    uom_type_denominator = ('time',)

    def __str__(self):
        return 'Cubic_Meter_Per_Second'


class BaseVelocity(BaseUom):
    uom_type_numerator = ('length',)
    uom_type_denominator = ('time',)

    def __str__(self):
        return 'Meter_Per_Second'


class BaseForce(BaseUom):
    uom_type_numerator = ('mass', 'length')
    uom_type_denominator = ('time', 'time')

    def __str__(self):
        return 'Newton'


class BasePower(BaseUom):
    uom_type_numerator = ('mass', 'length', 'length')
    uom_type_denominator = ('time', 'time', 'time')

    def __str__(self):
        return 'Watt'


class BaseEnergy(BaseUom):
    uom_type_numerator = ('mass', 'length', 'length')
    uom_type_denominator = ('time', 'time')

    def __str__(self):
        return 'Joule'


NoUom = BaseNoUom(lambda value: value, lambda value: value)
NoUomx10 = BaseNoUom(lambda value: value * 10, lambda value: value / 10)
NoUomx100 = BaseNoUom(lambda value: value * 100, lambda value: value / 100)
NoUomx1000 = BaseNoUom(lambda value: value * 1000, lambda value: value / 1000)
NoUomx10000 = BaseNoUom(lambda value: value * 10000, lambda value: value / 10000)
NoUomx100000 = BaseNoUom(lambda value: value * 100000, lambda value: value / 100000)
NoUomx1000000 = BaseNoUom(lambda value: value * 1000000, lambda value: value / 1000000)
NoUomx10000000 = BaseNoUom(lambda value: value * 10000000, lambda value: value / 10000000)
NoUomx100000000 = BaseNoUom(lambda value: value * 100000000, lambda value: value / 100000000)
NoUomx1000000000 = BaseNoUom(lambda value: value * 1000000000, lambda value: value / 1000000000)

Meter = BaseLength(lambda value: value, lambda value: value)
Yard = BaseLength(lambda value: value * .9144, lambda value: value / .9144)
Feet = Yard * BaseUom(lambda value: value / 3, lambda value: value * 3)
Inch = Feet * BaseUom(lambda value: value / 12, lambda value: value * 12)
Mile = Feet * BaseUom(lambda value: value * 5280, lambda value: value / 5280)
Chain = Yard * BaseUom(lambda value: value * 22, lambda value: value / 22)
Furlong = Yard * BaseUom(lambda value: value * 220, lambda value: value / 220)
MicroMeter = Meter / NoUomx1000000
MilliMeter = Meter / NoUomx1000
CentiMeter = Meter / NoUomx100
HectoMeter = Meter * NoUomx100
KiloMeter = Meter * NoUomx1000
MegaMeter = Meter * NoUomx1000000

Second = BaseTime(lambda value: value, lambda value: value)
Minute = BaseTime(lambda value: value * 60, lambda value: value / 60)
Hour = BaseTime(lambda value: value * 3600, lambda value: value / 3600)
Day = BaseTime(lambda value: value * 3600 * 24, lambda value: value / 3600 / 24)

Kelvin = BaseTemperature(lambda value: value, lambda value: value)
Centigrade = BaseTemperature(lambda value: value + 273.15, lambda value: value - 273.15)
Centigrade40 = Centigrade * BaseUom(lambda value: value - 40, lambda value: value + 40)
Centigrade40x01 = Centigrade * BaseUom(lambda value: (value / 10) - 40, lambda value: (value + 40) * 10)
Fahrenheit = Centigrade * BaseUom(lambda value: (value - 32) * (5 / 9), lambda value: value * (9 / 5) + 32)
MicroKelvin = Kelvin / NoUomx1000000
MilliKelvin = Kelvin / NoUomx1000
CentiKelvin = Kelvin / NoUomx100
HectoKelvin = Kelvin * NoUomx100
KiloKelvin = Kelvin * NoUomx1000
MegaKelvin = Kelvin * NoUomx1000000

KelvinDiff = BaseTemperatureDifference(lambda value: value, lambda value: value)
CentigradeDiff = BaseTemperatureDifference(lambda value: value, lambda value: value)
FahrenheitDiff = BaseTemperatureDifference(lambda value: (5 / 9), lambda value: value * (9 / 5))

KiloGram = BaseMass(lambda value: value, lambda value: value)
Ounce = BaseMass(lambda value: value * 28.349523125 / 1000, lambda value: value / 28.349523125 * 1000)
Pound = Ounce * BaseUom(lambda value: value * 16, lambda value: value / 16)
MicroGram = KiloGram / NoUomx1000000000
MilliGram = KiloGram / NoUomx1000000
CentiGram = KiloGram / NoUomx100000
Gram = KiloGram / NoUomx1000
HectoGram = KiloGram / NoUomx10
MegaGram = KiloGram * NoUomx1000

Ampere = BaseCurrent(lambda value: value, lambda value: value)
MicroAmpere = Ampere / NoUomx1000000
MilliAmpere = Ampere / NoUomx1000
CentiAmpere = Ampere / NoUomx100
HectoAmpere = Ampere * NoUomx100
KiloAmpere = Ampere * NoUomx1000
MegaAmpere = Ampere * NoUomx1000000

Radian = BaseAngle(lambda value: value, lambda value: value)
Degree = BaseAngle(lambda value: value * math.pi / 180, lambda value: value / math.pi * 180)

Hertz = BaseFrequency(lambda value: value, lambda value: value)
MicroHertz = Hertz / NoUomx1000000
MilliHertz = Hertz / NoUomx1000
CentiHertz = Hertz / NoUomx100
HectoHertz = Hertz * NoUomx100
KiloHertz = Hertz * NoUomx1000
MegaHertz = Hertz * NoUomx1000000

Volt = BaseVolt(lambda value: value, lambda value: value)
MicroVolt = Volt / NoUomx1000000
MilliVolt = Volt / NoUomx1000
CentiVolt = Volt / NoUomx100
HectoVolt = Volt * NoUomx100
KiloVolt = Volt * NoUomx1000
MegaVolt = Volt * NoUomx1000000

Pascal = BasePressure(lambda value: value, lambda value: value)
Psi = Pascal * BaseUom(lambda value: value * 6894.76, lambda value: value / 6894.76)
MicroPascal = Pascal / NoUomx1000000
MilliPascal = Pascal / NoUomx1000
CentiPascal = Pascal / NoUomx100
HectoPascal = Pascal * NoUomx100
KiloPascal = Pascal * NoUomx1000
MegaPascal = Pascal * NoUomx1000000
Bar = KiloPascal * NoUomx100
MicroBar = Bar / NoUomx1000000
MilliBar = Bar / NoUomx1000
CentiBar = Bar / NoUomx100
HectoBar = Bar * NoUomx100
KiloBar = Bar * NoUomx1000
MegaBar = Bar * NoUomx1000000
MeterOfHead = Bar * BaseUom(lambda value: value / 10.19977334, lambda value: value * 10.19977334)
InchOfMercury = Bar * BaseUom(lambda value: value / 29.529983, lambda value: value * 29.529983)

Liter = BaseVolume(lambda value: value / 1000, lambda value: value * 1000)  # convert to m^3
Gallon = Liter * BaseUom(lambda value: value * 3.785411784, lambda value: value / 3.785411784)
FluidOunce = Gallon * BaseUom(lambda value: value / 128, lambda value: value * 128)
Gallonx1000 = Gallon * NoUomx1000
MicroLiter = Liter / NoUomx1000000
MilliLiter = Liter / NoUomx1000
CentiLiter = Liter / NoUomx100
HectoLiter = Liter * NoUomx100
KiloLiter = Liter * NoUomx1000
MegaLiter = Liter * NoUomx1000000

Newton = BaseForce(lambda value: value, lambda value: value)
PoundForce = Newton * BaseUom(lambda value: value * 4.448222, lambda value: value / 4.448222)
MicroNewton = Newton / NoUomx1000000
MilliNewton = Newton / NoUomx1000
CentiNewton = Newton / NoUomx100
HectoNewton = Newton * NoUomx100
KiloNewton = Newton * NoUomx1000
MegaNewton = Newton * NoUomx1000000

Watt = BasePower(lambda value: value, lambda value: value)
HorsePower = Watt * BaseUom(lambda value: value * 745.69987158227, lambda value: value / 745.69987158227)
MicroWatt = Watt / NoUomx1000000
MilliWatt = Watt / NoUomx1000
CentiWatt = Watt / NoUomx100
HectoWatt = Watt * NoUomx100
KiloWatt = Watt * NoUomx1000
MegaWatt = Watt * NoUomx1000000

Joule = BaseEnergy(lambda value: value, lambda value: value)
Calorie = Joule * BaseUom(lambda value: value * 4.1858, lambda value: value / 4.1858)
Btu = Joule * BaseUom(lambda value: value * 1055.06, lambda value: value / 1055.06)
MicroJoule = Joule / NoUomx1000000
MilliJoule = Joule / NoUomx1000
CentiJoule = Joule / NoUomx100
HectoJoule = Joule * NoUomx100
KiloJoule = Joule * NoUomx1000
MegaJoule = Joule * NoUomx1000000


MeterPerSecond = BaseVelocity(lambda value: value, lambda value: value)
CubicMeterPerSecond = BaseFlow(lambda value: value, lambda value: value)
SquareMeter = BaseArea(lambda value: value, lambda value: value)

Acre = Chain * Furlong
Hectare = Acre * NoUomx100

PartsPerMillion = NoUom
PartsPerBillion = PartsPerMillion * NoUomx1000
PartsPerThousand = PartsPerMillion / NoUomx1000
