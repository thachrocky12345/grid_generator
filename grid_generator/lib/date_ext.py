from datetime import datetime, timedelta
import psycopg2
import dateutil.parser


def datetime_range(from_date, to_date, interval=timedelta(days=1)):
    if not isinstance(from_date, datetime):
        raise TypeError("from_date argument must be a datetime, not {0}".format(type(from_date)))
    if not isinstance(to_date, datetime):
        raise TypeError("to_date argument must be a datetime, not {0}".format(type(to_date)))
    if not isinstance(interval, timedelta):
        raise TypeError("interval argument must be a timedelta, not {0}".format(type(interval)))
    if interval == timedelta(0):
        raise ValueError("interval must not be 0")
    if to_date <= from_date:
        if interval > timedelta():
            raise StopIteration
        while from_date > to_date:
            yield from_date
            from_date = from_date + interval
    if to_date > from_date:
        if interval < timedelta():
            raise StopIteration
        while from_date < to_date:
            yield from_date
            from_date = from_date + interval


def totalseconds(datetime_ts):
    if not isinstance(datetime_ts, timedelta):
        raise TypeError("datetime_ts argument must be a timedelta, not {0}".format(type(datetime_ts)))
    return (datetime_ts.microseconds + (datetime_ts.seconds + datetime_ts.days * 24 * 3600) * 1000000) / 1000000  # python 2.7 can use the total seconds method


def timestamp(datetime_ts):
    datetime_ts = datetimetz(datetime_ts)
    d = datetime_ts - datetimetz(datetime(1970, 1, 1))
    return totalseconds(d)


def now(tz=psycopg2.tz.FixedOffsetTimezone()):
    return datetime.now(tz)


def min():
    return datetimetz(datetime.min)


def get_tz(datetime_timedelta):
    total = totalseconds(datetime_timedelta)
    return psycopg2.tz.FixedOffsetTimezone(total / 60)


def datetimetz(datetime_stamp, tz=psycopg2.tz.FixedOffsetTimezone()):
    return datetime_stamp.replace(tzinfo=tz)


def parse_isoformat(string):
    timestamp = dateutil.parser.parse(string)
    try:
        old_tz_info = timestamp.tzinfo.utcoffset(None)
    except:
        old_tz_info = timedelta(0)

    new_tz_info = psycopg2.tz.FixedOffsetTimezone(totalseconds(old_tz_info) / 60)
    timestamp = timestamp.replace(tzinfo=new_tz_info)
    return timestamp
