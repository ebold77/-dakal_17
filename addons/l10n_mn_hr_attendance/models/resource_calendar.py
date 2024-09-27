from datetime import date, datetime, timedelta
import copy
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def get_lunch_hours(self):
        self.ensure_one()
        hours = 0
        monday_morning = self.attendance_ids.filtered(lambda a: a.dayofweek == '0' and a.day_period == 'morning')
        monday_afternoon = self.attendance_ids.filtered(lambda a: a.dayofweek == '0' and a.day_period == 'afternoon')
        if monday_morning and monday_afternoon:
            hours = monday_afternoon.hour_from - monday_morning.hour_to
        return hours

    def get_lunch_interval(self):
        self.ensure_one()
        start = end = 0
        monday_morning = self.attendance_ids.filtered(lambda a: a.dayofweek == '0' and a.day_period == 'morning')
        monday_afternoon = self.attendance_ids.filtered(lambda a: a.dayofweek == '0' and a.day_period == 'afternoon')
        if monday_morning and monday_afternoon:
            start = monday_morning.hour_to
            end = monday_afternoon.hour_from
        return start, end