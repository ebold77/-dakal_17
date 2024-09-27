# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
import pytz
import importlib as il
from dateutil import rrule
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


def get_user_timezone(user):
    # get user time zone
    user_time_zone = pytz.UTC
    if user.sudo().tz:
        user_time_zone = pytz.timezone(user.sudo().tz)
    # else:
    #     raise ValidationError(_('Please set your time zone!'))
    return user_time_zone


def get_day_by_user_timezone(day, user):
    # Хэрэглэгчийн timezone-рүү огноог шилжүүлж буцаах функц
    day = str(day)[:19] if len(str(day)) > 10 else str(day) + " 00:00:00"
    return get_user_timezone(user).localize(datetime.strptime(day, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(get_user_timezone(user)).replace(tzinfo=None)


def float_to_hours_minutes(float_time):
    float_time = 0 if float_time == 24 else float_time
    result = '{0:02.0f}:{1:02.0f}'.format(*divmod(float_time * 60, 60))
    if result.split(":")[1] == '60':
        hour = str(int(result.split(":")[0]) + 1)
        minute = "00"
        result = hour + ":" + minute
    return result


def change_date_to_user_tz(day, user):
    day = str(day) if len(str(day)) > 10 else str(day) + " 00:00:00"
    day = datetime.strptime(day, DEFAULT_SERVER_DATETIME_FORMAT)
    return day.replace(tzinfo=pytz.utc).astimezone(get_user_timezone(user))


def get_day_like_display(day, user):
    # ERP дээр тухайн огноог хэрхэн харуулж байгааг тооцоолж буцаах функц:
    # Хэрэглэгчийн timezone-с хамаараад харуулж байгаа болон өгөгдлийн сан руу хадгалж байгаа цагууд зөрдөг тул тухайн зөрүүг тооцоолж өдөр тооцоход уг функцыг ашиглах
    if not day:
        return False
    offset = get_user_timezone(user).utcoffset(datetime.strptime(str(day)[:19], DEFAULT_SERVER_DATETIME_FORMAT))  # utcoffset -> UTC +09 гэдгийн '09'-г авах
    display_day = datetime.strptime(str(day)[:19], DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(hours=+int(str(offset).split(":")[0]), minutes=+int(str(offset).split(":")[1]), seconds=+int(str(offset).split(":")[2]))
    return display_day


def get_display_day_to_user_day(day, user):
    # ERP дээр тухайн огноог хэрхэн харуулж байгааг тоооцоолж буцаах функц:
    # Хэрэглэгчийн timezone-с хамаараад харуулж байгаа болон өгөгдлийн сан руу хадгалж байгаа цагууд зөрдөг тул тухайн зөрүүг тооцоолж өдөр тооцоход уг функцыг ашиглах
    if not day:
        return False
    offset = get_user_timezone(user).utcoffset(datetime.strptime(str(day), DEFAULT_SERVER_DATETIME_FORMAT))  # utcoffset -> UTC +09 гэдгийн '09'-г авах
    display_day = datetime.strptime(str(day), DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(hours=-int(str(offset).split(":")[0]), minutes=-int(str(offset).split(":")[1]), seconds=-int(str(offset).split(":")[2]))
    return display_day


def get_day_to_display_timezone(day, user):
    # PLS_FIX_ME: UTC -09 гэдгийг тооцож чадаж байгаа эсэхийг мэдэхгүй байна. Одоогоор ашиглагдахгүй тул орхив. Засах !!!
    offset = get_user_timezone(user).utcoffset(datetime.strptime(str(day), DEFAULT_SERVER_DATETIME_FORMAT))  # utcoffset -> UTC +09 гэдгийн '09'-г авах
    display_day = datetime.strptime(str(day), DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(hours=-int(str(offset).split(":")[0]), minutes=-int(str(offset).split(":")[1]), seconds=-int(str(offset).split(":")[2]))
    return display_day


def get_day_to_display_timezone_from_floattime(date, float_time, user):
    # 24:00 цаг гэж байхгүй тул -> дараа өдрийн 00:00 цагт шилжүүлэх
    if float_time == 24:
        float_time = 0
        date += relativedelta(days=1)
    result = float_to_hours_minutes(float_time)
    date = get_day_to_display_timezone(get_day_like_display(date, user).replace(hour=int(str(result).split(":")[0]), minute=int(str(result).split(":")[1]), second=0), user) if date else False
    return date


def get_day_like_display_from_floattime(date, float_time, user):
    # 24:00 цаг гэж байхгүй тул -> дараа өдрийн 00:00 цагт шилжүүлэх
    if float_time == 24:
        float_time = 0
        date += relativedelta(days=1)
    result = float_to_hours_minutes(float_time)
    date = get_day_like_display(date, user).replace(hour=int(str(result).split(":")[0]), minute=int(str(result).split(":")[1]), second=0)
    return date


def get_difference_btwn_2date(date1, date2, context={}):
    if not (date1 and date2):
        return 0
    type = 'hour'
    if 'diff_type' in context and context['diff_type'] != 'hour':
        type = context['diff_type']

    max_date, min_date = date1, date2
    if date2 > date1:
        max_date, min_date = date2, date1

    diff = fields.Datetime.from_string(str(max_date)) - fields.Datetime.from_string(str(min_date))
    if diff:
        if type == 'hour':
            return float(diff.days) * 24 + (float(diff.seconds) / 3600)
        elif type == 'minute':
            return float(diff.days) * 24 * 60 + (float(diff.seconds) / 60)
    else:
        return 0


def get_difference_btwn_2date_intervals(date1_start, date1_end, date2_start, date2_end, context={}):
    type = 'hour'
    if 'diff_type' in context and context['diff_type'] != 'hour':
        type = context['diff_type']

    diff = False
    from_date, to_date = False, False
    date1_start, date1_end, date2_start, date2_end = str(date1_start), str(date1_end), str(date2_start), str(date2_end)

    if date1_start <= date2_start:
        if date1_end <= date2_end:
            from_date, to_date = date2_start, date1_end
        else:
            from_date, to_date = date2_start, date2_end
    else:
        if date1_end <= date2_end:
            from_date, to_date = date1_start, date1_end
        else:
            from_date, to_date = date1_start, date2_end

    diff = fields.Datetime.from_string(str(to_date)) - fields.Datetime.from_string(str(from_date))
    if from_date and to_date and diff:
        if type == 'hour':
            return float(diff.days) * 24 + (float(diff.seconds) / 3600)
        elif type == 'minute':
            return float(diff.days) * 24 * 60 + (float(diff.seconds) / 60)
    else:
        return 0
    

def get_duplicated_day_domain(domain_day_start, domain_day_end, st_date, end_date, user):
    if not (domain_day_start and domain_day_end and st_date and end_date):
        return ''
    
    st_date = str(st_date)
    end_date = str(end_date)
    
    domain = [
        '|','|','|',
       '&', (domain_day_start, '>=', st_date),
       (domain_day_start, '<=', end_date),
       '&', (domain_day_start, '<=', st_date),
       (domain_day_end, '>=', end_date),
       '&', (domain_day_end, '>=', st_date),
       (domain_day_end, '<=', end_date), 
       '&', (domain_day_start, '>=', st_date),
       (domain_day_end, '<=', end_date)
    ]
    
    return domain

def get_duplicated_hours_by_time_intervals(time_intervals, st_date, end_date):
    # Огнооны интервиалын st_date болон end_date огнооны хоорондох хугацаанд давхцсан цагийг олж буцаана.
    duplicated_hours = 0
    
    for time_interval in time_intervals:
        diff = get_difference_btwn_2date_intervals(st_date, end_date, interval_st_date, interval_end_date)
        if diff > 0:
            duplicated_hours += diff
            
    return duplicated_hours

def get_duplicated_hours_between_intervals(time_intervals_from, time_intervals_to):
    # Огнооны интервиалуудын давхцсан цагийг олж буцаана.
    duplicated_hours = 0
    
    if time_intervals_from and time_intervals_to:
        for time_interval_from in time_intervals_from:
            for time_interval_to in time_intervals_to:
                diff = get_difference_btwn_2date_intervals(time_interval_from[0], time_interval_from[1], time_interval_to[0], time_interval_to[1])
                if diff > 0:
                    duplicated_hours += diff
                            
    return duplicated_hours

def get_available_min_max_date(from_date, to_date, dates):
                
    min_date, max_date = False, False
    from_date = datetime.strptime(str(from_date), DEFAULT_SERVER_DATETIME_FORMAT)
    to_date = datetime.strptime(str(to_date), DEFAULT_SERVER_DATETIME_FORMAT)
    available_dates = []
    
    for date in dates:
        date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
        if from_date <= date and date <= to_date:
            available_dates.append(date)
        else:
            available_dates.append(False)
    
    if available_dates and len(available_dates) > 0:
        
        for available_date in available_dates:
            if available_date:
                min_date, max_date = available_date, available_date
                break
                
        for available_date in available_dates:
            if available_date and available_date < min_date:
                min_date = available_date
            if available_date and available_date > max_date:
                max_date = available_date
                 
    return min_date if min_date else False, max_date if max_date else False

def get_duplication_interval(f1, t1, f2, t2):
    # Давхцлын интервалын 2 өдрийг тооцоолж буцаана
    from_date, to_date = False, False

    if f1 <= f2 and t1 <= t2 and f2 <= t1:
        #  f1___________________t1
        #           f2___________________t2
        from_date, to_date = f2, t1
    elif f1 >= f2 and t1 >= t2 and f1 <= t2:
        #           f1___________________t1
        #  f2___________________t2
        from_date, to_date = f1, t2
    elif f1 >= f2 and t1 <= t2 and f1 <= t1:
        #           f1_____t1
        #  f2___________________t2
        from_date, to_date = f1, t1
    elif f1 <= f2 and t1 >= t2 and f2 <= t2:
        #  f1___________________t1
        #           f2_____t2
        from_date, to_date = f2, t2

    return from_date, to_date
