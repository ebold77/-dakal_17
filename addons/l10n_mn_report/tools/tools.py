# -*- coding: utf-8 -*-
from datetime import datetime, timedelta


def remove_custom(list_data, remove_value=['', None]):  # , is_not=True):
    if not isinstance(remove_value, (list, tuple)):
        remove_value = [remove_value]

    for val in remove_value:
        temp_data = []
        if list_data:
            for data in list_data:
                if data != val:
                    temp_data.append(data)
        list_data = temp_data
    return list_data


def str_tuple(*args):
    value = []
    for val in args:
        if val:
            if isinstance(val, (list, tuple)):
                new_val = remove_custom(val, ['', None])
                value.extend(list(new_val))
            else:
                value.append(str(val))
    value = list(set(value))
    if value:
        if isinstance(value, (tuple, list)):
            return str(tuple(map(str, value))).replace(',)', ')')
        else:
            return '(\'' + str(value) + '\')'
    else:
        return 'NULL'


def first_date(date_str):
    return date_str + ' 00:00:00'


def last_date(date_str):
    return date_str + ' 23:59:59'


def get_date(date_str, is_first=False):
    _format = '%Y-%m-%d %H:%M:%S'
    if validate_date(date_str, _format):
        date_str = date_str[0:10]
    if is_first:
        date_str = first_date(date_str)
    else:
        date_str = last_date(date_str)
    return date_str


def get_day(date_str):
    if validate_date(date_str):
        return date_str[0:10]
    else:
        return date_str


def add_hour(datetime_str, add_hour=8):
    _format = '%Y-%m-%d %H:%M:%S'

    date_obj = datetime.strptime(datetime_str, _format)
    date_obj += timedelta(hours=add_hour)
    return date_obj.strftime(_format)


def diff_date(date_str1, date_str2):
    _format = '%Y-%m-%d'
    a = datetime.strptime(date_str1, _format)
    b = datetime.strptime(date_str2, _format)
    delta = None
    if a > b:
        delta = a - b
    else:
        delta = b - a
    return delta.days


def calc_workday(date_start, date_end):
    if isinstance(date_start, str):
        date_start = str_to_date(date_start)
    if isinstance(date_end, str):
        date_end = str_to_date(date_end)
    daygenerator = (date_start + timedelta(x + 1) for x in xrange((date_end - date_start).days))
    return sum(1 for day in daygenerator if is_workday(day))


def is_workday(date):
    if isinstance(date, str):
        date = str_to_date(date)
    return date.weekday() < 5


def daterange(start_date, end_date):
    if isinstance(start_date, str):
        start_date = str_to_date(start_date)
    if isinstance(end_date, str):
        end_date = str_to_date(end_date)
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def str_to_date(date_str, _format="%Y-%m-%d %H:%M:%S"):
    if isinstance(date_str, str):
        if len(date_str) <= 10:
            _format = _format[0:10]
        return datetime.strptime(date_str, _format)
    else:
        return date_str


def validate_date(date, _format="%Y-%m-%d %H:%M:%S"):
    try:
        datetime.strptime(date, _format)
        return True
    except ValueError:
        return False


def fdict_to_dict(fdict):
    ddict = {}
    if not fdict:
        return None
    for key in fdict.keys():
        ddict[key] = fdict[key]
    return ddict
