from base import  Dto, DtoInteger, DtoTimestamp, DtoUom, DtoText

from lib import date_ext, math_ext
import base64
from twisted.web import client
import xml.etree.ElementTree
import urllib
import math
from datetime import timedelta, datetime
import uom

URL_BASE = "https://lindsay2410629:sCUBe9NrJ6cS9tfM@weather.dtn.com/basic/rest-3.4/obsfcst.wsgi"  # Remove "pre-" and set to production API when provisioned
DTN_DOC = 'http://weather.dtn.com/rest-3.4/doc/'  # Remove "pre-" and set to production API when provisioned


class DtoFieldWeather(Dto):
    def __init__(self, **kwargs):
        Dto.__init__(self)
        self.add_attr('account_device_id', DtoInteger(), read_only=True)
        self.add_attr('max_temperature', DtoUom(uom.Kelvin))
        self.add_attr('min_temperature', DtoUom(uom.Kelvin))
        self.add_attr('rainfall', DtoUom(uom.Meter))
        self.add_attr('evapotranspiration', DtoUom(uom.Meter))
        self.add_attr('condition', DtoText())
        self.add_attr('temperature', DtoUom(uom.Kelvin))
        self.add_attr('precipitation_probability', DtoUom(uom.NoUom))
        self.add_attr('wind_speed', DtoUom(uom.MeterPerSecond))
        self.add_attr('wind_gust', DtoUom(uom.MeterPerSecond))
        self.add_attr('wind_direction', DtoUom(uom.NoUom))
        self.add_attr('relative_humidity', DtoUom(uom.NoUom))
        self.add_attr('solar_radiation', DtoUom(uom.Watt / uom.Meter ** 2))
        self.add_attr('max_relative_humidity', DtoUom(uom.NoUom))
        self.add_attr('min_relative_humidity', DtoUom(uom.NoUom))
        self.add_attr('temperature_feels_like', DtoUom(uom.Kelvin))
        self.add_attr('code', DtoInteger())
        self.add_attr('precipitation_type', DtoText())
        self.add_attr('created', DtoTimestamp(), nullable=False, has_default=True)
        self.update(**kwargs)



class HourlyForecastDb(object):
    def __init__(self, start_time, end_time, account_device_id, db):
        self.db = db
        self.start_time = start_time
        self.end_time = end_time
        self.account_device_id = account_device_id
        self.dtod_weather = None

    def set_weather(self):
        pass

    def get_weather(self):
        pass






class MapperFieldWeather(object):
    def __init__(self, account_device_id, db):
        self.db = db
        self.account_device_id = account_device_id

    def update(self):
        pass

    def aggregate(self, dtod_weather):
        aggregated = {}
        for date in dtod_weather:
            aggregated_date = date.replace(hour=12)
            if aggregated_date not in aggregated:
                aggregated[date] = {}
                aggregated[date]['rain'] = []
                aggregated[date]['et'] = []
                aggregated[date]['temperature'] = []
                aggregated[date]['condition'] = []
                aggregated[date]['wind_speed'] = []
                aggregated[date]['relative_humidity'] = []
                aggregated[date]['temperature_feels_like'] = []
                aggregated[date]['wind_gust'] = []
                aggregated[date]['wind_direction'] = []
                aggregated[date]['solar_radiation'] = []

            aggregated[date]['rain'].append(dtod_weather[date].rainfall)
            aggregated[date]['et'].append(dtod_weather[date].evapotranspiration)
            aggregated[date]['temperature'].append(dtod_weather[date].temperature)
            aggregated[date]['condition'].append(dtod_weather[date].condition)
            aggregated[date]['wind_speed'].append(dtod_weather[date].wind_speed)
            aggregated[date]['relative_humidity'].append(dtod_weather[date].relative_humidity)
            aggregated[date]['temperature_feels_like'].append(dtod_weather[date].temperature_feels_like)
            aggregated[date]['wind_gust'].append(dtod_weather[date].wind_gust)
            aggregated[date]['wind_direction'].append(dtod_weather[date].wind_direction)
            aggregated[date]['solar_radiation'].append(dtod_weather[date].solar_radiation)

        dtod_aggregated = {}
        for date in aggregated:
            weather = DtoFieldWeather(account_device_id=self.account_device_id)
            dtod_aggregated[aggregated_date] = weather
            dtod_aggregated[aggregated_date].account_device_id = dtod_weather[date].account_device_id
            dtod_aggregated[aggregated_date].rainfall = sum(aggregated[date]['rain'])
            dtod_aggregated[aggregated_date].evapotranspiration = sum(aggregated[date]['et'])
            dtod_aggregated[aggregated_date].max_temperature = max(aggregated[date]['temperature'])
            dtod_aggregated[aggregated_date].min_temperature = min(aggregated[date]['temperature'])
            dtod_aggregated[aggregated_date].temperature = math_ext.avg(aggregated[date]['temperature'])
            dtod_aggregated[aggregated_date].condition = math_ext.mode(aggregated[date]['condition'])
            dtod_aggregated[aggregated_date].wind_speed = math_ext.avg(aggregated[date]['wind_speed'])
            dtod_aggregated[aggregated_date].max_relative_humidity = max(aggregated[date]['relative_humidity'])
            dtod_aggregated[aggregated_date].min_relative_humidity = min(aggregated[date]['relative_humidity'])
            dtod_aggregated[aggregated_date].relative_humidity = math_ext.avg(aggregated[date]['relative_humidity'])
            dtod_aggregated[aggregated_date].temperature_feels_like = math_ext.avg(aggregated[date]['temperature_feels_like'])
            dtod_aggregated[aggregated_date].wind_gust = max(aggregated[date]['wind_gust'])
            dtod_aggregated[aggregated_date].wind_direction = math_ext.mode(aggregated[date]['wind_direction'])
            dtod_aggregated[aggregated_date].solar_radiation = math_ext.avg(aggregated[date]['solar_radiation'])
        return dtod_aggregated

    def select_daily_weather_api(self, url, start_date, end_date):
        xml_data = urllib.urlopen(url).read()
        xml_data = xml.etree.ElementTree.fromstring(xml_data)
        ns = {'wx': DTN_DOC}
        xml_data = xml_data.find('wx:locationResponseList', ns)
        xml_data = xml_data.find('wx:locationResponse', ns)
        rainfall = xml_data.find('wx:precipitationAmountList', ns).find('wx:values', ns).text
        et = xml_data.find('wx:evapotranspirationList', ns).find('wx:values', ns).text
        max_temperature = xml_data.find('wx:maxTemperatureList', ns).find('wx:values', ns).text
        min_temperature = xml_data.find('wx:minTemperatureList', ns).find('wx:values', ns).text

        # solar_radiation = xml_data.find('wx:solarRadiationList', ns).find('wx:values', ns).text
        # max_relative_humidity = xml_data.find('wx:maxRelativeHumidityList', ns).text
        # min_relative_humidity = xml_data.find('wx:minRelativeHumidityList', ns).text
        # avg_wind_speed = xml_data.find('wx:avgWindSpeedList', ns).find('wx:values', ns).text

        rainfall = rainfall.split(' ')
        et = et.split(' ')
        max_temperature = max_temperature.split(' ')
        min_temperature = min_temperature.split(' ')
        # solar_radiation = solar_radiation.split(' ')
        # max_relative_humidity = max_relative_humidity.split(' ')
        # min_relative_humidity = min_relative_humidity.split(' ')
        # avg_wind_speed = avg_wind_speed.split(' ')

        rainfall = [uom.Uom(float(val), uom.Inch) for val in rainfall]
        et = [uom.Uom(float(val), uom.Inch) for val in et]
        max_temperature = [uom.Uom(float(val), uom.Fahrenheit) for val in max_temperature]
        min_temperature = [uom.Uom(float(val), uom.Fahrenheit) for val in min_temperature]
        # solar_radiation = [uom.Uom(float(val), uom.Watt / uom.Meter ** 2) for val in solar_radiation]
        # max_relative_humidity = [uom.Uom(float(val), uom.NoUomx100) for val in max_relative_humidity]
        # min_relative_humidity = [uom.Uom(float(val), uom.NoUomx100) for val in min_relative_humidity]
        # avg_wind_speed = [uom.Uom(float(val), uom.Mile / uom.Hour) for val in avg_wind_speed]

        dtod_weather = {}
        if end_date == start_date:
            end_date = start_date + timedelta(days=1)
        for index, date in enumerate(date_ext.datetime_range(start_date, end_date)):
            date = date.replace(hour=12)

            dto_weather = DtoFieldWeather(account_device_id=self.account_device_id)
            dto_weather.created = date
            dto_weather.max_temperature = max_temperature[index]
            dto_weather.min_temperature = min_temperature[index]
            dto_weather.rainfall = rainfall[index]
            dto_weather.evapotranspiration = et[index]
            # dto_weather.solar_radiation = solar_radiation[index]
            # dto_weather.max_relative_humidity = max_relative_humidity[index]
            # dto_weather.min_relative_humidity = min_relative_humidity[index]
            # dto_weather.wind_speed = avg_wind_speed[index]
            dtod_weather[date] = dto_weather
        return dtod_weather

    def select_hourly_weather_api(self, url, start_date, end_date, latitude, longitude, elevation):

        xml_data = urllib.urlopen(url).read()
        xml_data = xml.etree.ElementTree.fromstring(xml_data)
        ns = {'wx': DTN_DOC}
        xml_data = xml_data.find('wx:locationResponseList', ns)
        xml_data = xml_data.find('wx:locationResponse', ns)
        rainfall = xml_data.find('wx:precipitationAmountList', ns).find('wx:values', ns).text
        temperature = xml_data.find('wx:temperatureList', ns).find('wx:values', ns).text
        solar_radiation = xml_data.find('wx:solarRadiationList', ns).find('wx:values', ns).text
        relative_humidity = xml_data.find('wx:relativeHumidityList', ns).text
        wind_speed = xml_data.find('wx:windSpeedList', ns).find('wx:values', ns).text
        weather_condition = xml_data.find('wx:weatherDescriptionList', ns).text
        weather_code = xml_data.find('wx:weatherCodeList', ns).text
        feels_like = xml_data.find('wx:feelsLikeList', ns).find('wx:values', ns).text
        precipitation_type = xml_data.find('wx:precipitationTypeList', ns).text
        wind_gust = xml_data.find('wx:windGustList', ns).find('wx:values', ns).text
        wind_direction = xml_data.find('wx:windDirectionList', ns).find('wx:values', ns).text

        rainfall = rainfall.split(' ')
        temperature = temperature.split(' ')
        solar_radiation = solar_radiation.split(' ')
        relative_humidity = relative_humidity.split(' ')
        wind_speed = wind_speed.split(' ')
        weather_condition = weather_condition.split(' ')
        weather_code = weather_code.split(' ')
        feels_like = feels_like.split(' ')
        precipitation_type = precipitation_type.split(' ')
        wind_gust = wind_gust.split(' ')
        wind_direction = wind_direction.split(' ')

        rainfall = [uom.Uom(float(val), uom.Inch) for val in rainfall]
        temperature = [uom.Uom(float(val), uom.Fahrenheit) for val in temperature]
        solar_radiation = [uom.Uom(float(val), uom.Watt / uom.Meter ** 2) for val in solar_radiation]
        relative_humidity = [uom.Uom(float(val), uom.NoUomx100) for val in relative_humidity]
        wind_speed = [uom.Uom(float(val), uom.Mile / uom.Hour) for val in wind_speed]
        temperature_feels_like = [uom.Uom(float(val), uom.Fahrenheit) for val in feels_like]
        wind_gust = [uom.Uom(float(val), uom.Mile / uom.Hour) for val in wind_gust]
        wind_direction = [uom.Uom(float(val), uom.NoUom) for val in wind_direction]

        try:
            chance_of_rain = xml_data.find('wx:probabilityOfPrecipitationList', ns).text
            chance_of_rain = chance_of_rain.split(' ')
            chance_of_rain = [uom.Uom(float(val), uom.NoUomx100) for val in chance_of_rain]
        except:
            chance_of_rain = [None] * len(rainfall)

        dtod_weather = {}
        if end_date == start_date:
            end_date = start_date + timedelta(hours=1)
        for index, date in enumerate(date_ext.datetime_range(start_date, end_date, timedelta(hours=1))):
            dto_weather = DtoFieldWeather(account_device_id=self.account_device_id)
            dto_weather.created = date
            dto_weather.temperature = temperature[index]
            dto_weather.rainfall = rainfall[index]
            dto_weather.solar_radiation = solar_radiation[index]
            dto_weather.relative_humidity = relative_humidity[index]
            dto_weather.wind_speed = wind_speed[index]
            dto_weather.wind_gust = wind_gust[index]
            dto_weather.wind_direction = wind_direction[index]
            dto_weather.condition = weather_condition[index].replace('-', ' ')
            dto_weather.code = weather_code[index]
            dto_weather.temperature_feels_like = temperature_feels_like[index]
            dto_weather.precipitation_probability = chance_of_rain[index]
            dto_weather.precipitation_type = precipitation_type[index]
            evapotranspiration = self.ref_et_hourly(
                date,
                date + timedelta(hours=1),
                dto_weather.temperature.convert(uom.Centigrade),
                dto_weather.wind_speed.convert(uom.Meter / uom.Second),
                dto_weather.solar_radiation.convert(uom.MegaJoule / uom.Meter ** 2 / uom.Hour),
                dto_weather.relative_humidity.convert(uom.NoUomx100),
                latitude,
                longitude,
                elevation)
            dto_weather.evapotranspiration = uom.Uom(evapotranspiration, uom.MilliMeter)
            dtod_weather[date] = dto_weather
        return dtod_weather

    def adjusted_long(self, longitude):
        """
        calculate the adjusted longitude
        :param longitude: longitude of the field's center in decimal degrees - float
        :return: adjusted longitude
        """
        if longitude < 0:
            return abs(longitude)

        return 360 - longitude

    def central_longitude(self, longitude):
        """
        Calculate the longitude central
        :param longitude: longitude of the field's center in decimal degrees - float
        :return: longitude central - float
        """
        if longitude > 180 or longitude < -180:
            raise ValueError("longitude only between -180 and 180")

        mult = round(self.adjusted_long(longitude) / 15, 0)

        return (15 * mult) % 360

    def ref_et_hourly(self, start_date_time, end_date_time, temp, wind_speed, solar_rad, rel_hum, latitude, longitude, elevation):
        """
        calculate the hourly reference ET
        :param start_date_time: datetime stamp of the beginning of the hour - datetime
        :param end_date_time: datetime stamp of the end of the hour - datetime
        :param temp: average temperature for the given hour in degrees Celsius - float
        :param wind_speed: average wind speed for the hour in m/s - float
        :param solar_rad: total solar radiation for given hour in (MJ / m^2 * hour) - float
        :param rel_hum: average relative humidity for the given hour - float
        :param latitude: latitude of the field's center in decimal degrees - float
        :param longitude: longitude of the field's center in decimal degrees - float
        :return: hourly reference ET (mm) - float
        """
        rad_lat = latitude * (math.pi / 180)
        adj_lon = self.adjusted_long(longitude)
        center_lon = self.central_longitude(longitude)
        net_rad = self.short_radiation(solar_rad) - self.long_radiation(temp, solar_rad, rel_hum, elevation, start_date_time, end_date_time, rad_lat, adj_lon, center_lon)
        heat_flux = self.soil_heat_flux(start_date_time, end_date_time, rad_lat, adj_lon, center_lon, net_rad)
        delta = (4098 * 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))) / (temp + 237.3) ** 2
        psych_const = self.psych_constant(elevation)
        sat_vap_pressure = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
        ave_vap_pressure = sat_vap_pressure * rel_hum / 100
        ref_et1 = (0.408 * delta * (net_rad - heat_flux)) / (delta + psych_const * (1.0 + 0.34 * wind_speed))
        ref_et2 = (psych_const * (37.0 / (float(temp) + 273.0)) * wind_speed * (sat_vap_pressure - ave_vap_pressure)) / (delta + psych_const * (1.0 + 0.34 * wind_speed))
        return ref_et1 + ref_et2

    def short_radiation(self, solar_rad):
        """
        calculate net shortwave radiation
        :param solar_rad: solar radiation in (MJ / m^2 * hour) - float
        :return: net shortwave radiation (MJ / m^2 * hour) - float
        """
        return (1 - 0.23) * solar_rad

    def long_radiation(self, temp, solar_rad, rel_hum, elevation, start_date_time, end_date_time, rad_lat, adj_lon, center_lon):
        """
        calculate net longwave radiation
        :param temp: average temperature for the given hour in degrees Celsius - float
        :param solar_rad: solar radiation in (MJ / m^2 * hour) - float
        :param rel_hum: relative humidity in % - float
        :param elevation: elevation in meters - float
        :param start_date_time: datetime stamp of the beginning of the hour - datetime
        :param end_date_time: datetime stamp of the end of the hour - datetime
        :param rad_lat: latitude in radians  - float
        :param adj_lon: longitude in degrees west of GMT - float
        :param center_lon: longitude of the timezone center in degrees west of GMT - float
        :return: net longwave radiation in (MJ / m^2 * hour) - float
        """
        clear_sky_radiation = (0.75 + 2 * 10 ** -5 * elevation) * self.ext_radiation(start_date_time, end_date_time, rad_lat, adj_lon, center_lon)

        sol_ratio = solar_rad / clear_sky_radiation

        if sol_ratio > 1:
            sol_ratio = 1

        sat_vap_pressure = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
        ave_vap_pressure = sat_vap_pressure * rel_hum / 100

        return 2.043 * 10 ** -10 * (temp + 273) ** 4 * (0.34 - 0.14 * (ave_vap_pressure ** 0.5)) * (1.35 * sol_ratio - 0.35)

    def ext_radiation(self, start_date_time, end_date_time, rad_lat, adj_lon, center_lon):
        """
        calculate extraterrestrial radiation
        :param start_date_time: datetime stamp of the beginning of the hour - datetime
        :param end_date_time: datetime stamp of the end of the hour - datetime
        :param rad_lat: latitude in radians - float
        :param adj_lon: longitude in degrees west of GMT  - float
        :param center_lon: longitude of the timezone center in degrees west of GMT - float
        :return:
        """
        start_date = datetime(year=start_date_time.year, month=1, day=1)
        curr_date = datetime(year=start_date_time.year, month=start_date_time.month, day=start_date_time.day)
        day_of_year = curr_date - start_date
        solar_angle = self.solar_time_angle(start_date_time, end_date_time, adj_lon, center_lon)
        solar_decline = 0.409 * math.sin((2 * math.pi) / 365 * day_of_year.days - 1.39)
        inv_earth_dist = 1 + 0.033 * math.cos((2 * math.pi) / 365 * day_of_year.days)
        sunset_angle = math.acos(-math.tan(rad_lat) * math.tan(solar_decline))

        if abs(solar_angle) > sunset_angle:
            solar_angle1 = (sunset_angle - 0.655) - (math.pi / 24)
            solar_angle2 = (sunset_angle - 0.655) + (math.pi / 24)
        else:
            solar_angle1 = solar_angle - (math.pi / 24)
            solar_angle2 = solar_angle + (math.pi / 24)

        return (12 * 60 / math.pi) * 0.082 * inv_earth_dist * ((solar_angle2 - solar_angle1) * math.sin(rad_lat) * math.sin(solar_decline) + math.cos(rad_lat) * math.cos(solar_decline) * (math.sin(solar_angle2) - math.sin(solar_angle1)))

    def solar_time_angle(self, start_date_time, end_date_time, adj_lon, center_lon):
        """
        calculate solar time angle at midpoint of hour
        :param start_date_time: datetime stamp of the beginning of the hour - datetime
        :param end_date_time: datetime stamp of the end of the hour - datetime
        :param adj_lon: longitude in degrees west of GMT - float
        :param center_lon: longitude of the timezone center in degrees west of GMT - float
        :return: solar time angle at midpoint of the hour in [radians] - float
        """
        start_hour = start_date_time.hour
        end_hour = end_date_time.hour
        if end_hour == 0:
            end_hour = 24

        t_j = (float(start_hour) + float(end_hour)) / 2
        start_date = datetime(year=start_date_time.year, month=1, day=1)
        curr_date = datetime(year=start_date_time.year, month=start_date_time.month, day=start_date_time.day)
        day_of_year = curr_date - start_date
        b = (2 * math.pi * (day_of_year.days - 81)) / 364
        s_c = 0.1645 * math.sin(2 * b) - 0.1255 * math.cos(b) - 0.025 * math.sin(b)
        return (math.pi / 12) * ((t_j + 0.06667 * (center_lon - adj_lon) + s_c) - 12)

    def soil_heat_flux(self, start_date_time, end_date_time, rad_lat, adj_lon, center_lon, net_rad):
        """
        calculate soil heat flux
        :param start_date_time: datetime stamp of the beginning of the hour - datetime
        :param end_date_time: datetime stamp of the end of the hour - datetime
        :param rad_lat: latitude in radians - float
        :param adj_lon: longitude in degrees west of GMT - float
        :param center_lon: longitude of the timezone center in degrees west of GMT - float
        :param net_rad: net radiation in [MJ / (m^2 * hour)] - float
        :return: soil heat flux in [MJ / (m^2 * hour)] - float
        """
        start_date = datetime(year=start_date_time.year, month=1, day=1)
        curr_date = datetime(year=start_date_time.year, month=start_date_time.month, day=start_date_time.day)
        day_of_year = curr_date - start_date
        solar_angle = self.solar_time_angle(start_date_time, end_date_time, adj_lon, center_lon)
        solar_decline = 0.409 * math.sin((2 * math.pi) / 365 * day_of_year.days - 1.39)
        sunset_angle = math.acos(-math.tan(rad_lat) * math.tan(solar_decline))
        if abs(solar_angle) <= sunset_angle:
            return 0.1 * net_rad

        return 0.5 * net_rad

    def psych_constant(self, elevation):
        """
        calculate psychrometic constant
        :param elevation: elevation in meters - float
        :return: psychrometric constant in [kPa / degrees C]
        """
        return 0.665 * 10 ** -3 * 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26


    def select_weather_daily_observed(self, start_date, end_date, longitude, latitude):
        url = URL_BASE + "?dataType=DailyInterpolatedObservation&dataTypeMode=0002&startDate={start_date}&endDate={end_date}&latitude={latitude}&longitude={longitude}"
        url = url.format(start_date=urllib.quote(start_date.isoformat()), end_date=urllib.quote(end_date.isoformat()), longitude=longitude, latitude=latitude)
        return self.select_daily_weather_api(url, start_date, end_date)


    def select_weather_daily_forecast(self, start_date, end_date, longitude, latitude):
        url = URL_BASE + "?dataType=DailyInterpolatedForecast&dataTypeMode=0002&startDate={start_date}&endDate={end_date}&latitude={latitude}&longitude={longitude}"
        url = url.format(start_date=urllib.quote(start_date.isoformat()), end_date=urllib.quote(end_date.isoformat()), longitude=longitude, latitude=latitude)
        return self.select_daily_weather_api(url, start_date, end_date)


    def select_weather_daily_normal(self, start_date, end_date, longitude, latitude):
        url = URL_BASE + "?dataType=DailyInterpolatedNormal&dataTypeMode=0002&startDate={start_date}&endDate={end_date}&latitude={latitude}&longitude={longitude}"
        url = url.format(start_date=urllib.quote(start_date.isoformat()), end_date=urllib.quote(end_date.isoformat()), longitude=longitude, latitude=latitude)
        return self.select_daily_weather_api(url, start_date, end_date)


    def select_weather_hourly_observed(self, start_date, end_date, longitude, latitude, elevation):
        url = URL_BASE + "?dataType=HourlyInterpolatedObservation&dataTypeMode=001&startDate={start_date}&endDate={end_date}&latitude={latitude}&longitude={longitude}"
        url = url.format(start_date=urllib.quote(start_date.isoformat()), end_date=urllib.quote(end_date.isoformat()), longitude=longitude, latitude=latitude)
        return self.select_hourly_weather_api(url, start_date, end_date, latitude, longitude, elevation)


    def select_weather_hourly_forecast(self, start_date, end_date, longitude, latitude, elevation):
        # can only ask for 7 days at a time
        dtod_weather = {}
        for date in date_ext.datetime_range(start_date, end_date, timedelta(days=7)):
            date_end = date + timedelta(days=7)
            if date_end > end_date:
                date_end = end_date
            url = URL_BASE + "?dataType=HourlyInterpolatedForecast&dataTypeMode=001&startDate={start_date}&endDate={end_date}&latitude={latitude}&longitude={longitude}"
            url = url.format(start_date=urllib.quote(date.isoformat()), end_date=urllib.quote(date_end.isoformat()), longitude=longitude, latitude=latitude)

            dtod = self.select_hourly_weather_api(url, start_date, end_date, latitude, longitude, elevation)
            dtod_weather.update(dtod)

        return dtod_weather


