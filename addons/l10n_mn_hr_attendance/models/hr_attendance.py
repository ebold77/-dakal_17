# -*- coding: utf-8 -*-

from datetime import datetime, time

import pytz
from lxml import etree

from odoo import api, fields, models, exceptions, _
from odoo.addons.l10n_mn_hr_attendance.models.time_helper import *
from odoo.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    identification_id = fields.Char(related='employee_id.identification_id', store=True, readonly=False, string='Identification No') # Импортлохын тулд readonly=False байх хэрэгтэй
    in_device_name = fields.Char("In device Name")
    out_device_name = fields.Char("Out device Name")
    company_id = fields.Many2one('res.company', readonly=True, copy=True, string="Employee company",
                                 index=True, default=lambda self: self.env.company.id)
    in_time = fields.Char("Check-in time", compute='compute_check_in_time', store=True, readonly=True, group_operator="min")
    out_time = fields.Char("Check-out time", compute='compute_check_out_time', store=True, readonly=True, group_operator="max")
    time_lag = fields.Float(string='Time Lag', compute='_compute_time_lag', store=True, readonly=True)
    total_attendance_hours = fields.Float(compute='compute_total_attendance_hours', store=True, readonly=True, string='Total attendance(by hour)')
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id", store=True, readonly=True)
    is_attendance_repair = fields.Boolean(default=False)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('check_in')
    def _compute_time_lag(self):
        for attendance in self:
            weekday = attendance.check_in.weekday()
            resource_calendar_id = self.employee_id.resource_calendar_id
            
            for line in resource_calendar_id.attendance_ids:

                if int(line.dayofweek) == int(weekday) and line.day_period =='morning':
                    chech_time = line.hour_from
                    
                    result = '{0:02.0f}:{1:02.0f}'.format(*divmod(chech_time * 60, 60))
                    check_time_object = datetime.strptime(result, '%H:%M').time()
                    time_object = datetime.strptime(attendance.check_in.strftime("%H:%M"), '%H:%M').time()
                   
                    result = (datetime.combine(attendance.check_in, time_object) + timedelta(hours=8, minutes=0)).time()
                   
                    if result.hour >= check_time_object.hour:
                        lag_t = time(result.hour - check_time_object.hour, result.minute - check_time_object.minute)
                        lag_time_sec = lag_t.hour*3600 + lag_t.minute*60
                        attendance.time_lag = lag_time_sec/3600

    @api.model
    def create(self, vals):
        # Ирц үүсгэхэд компаниа ажилтнаасаа авдаг болгов.
        if 'company_id' not in vals.keys() and 'employee_id' in vals.keys():
            emp = self.env['hr.employee'].sudo().browse(vals['employee_id'])
            if emp and emp.sudo().company_id:
                vals['company_id'] = emp.company_id.sudo().id
        # Ялгах дугаараар импортлох боломжтой болгов.
        if 'identification_id' in vals.keys() and not 'employee_id' in vals.keys():
            employee_id = self.env['hr.employee'].search([('identification_id', '=', vals['identification_id'])])
            if employee_id:
                vals['employee_id'] = employee_id.id
        return super(HrAttendance, self).create(vals)

    # Ирсэн цагийг тооцоолж хадгална.
    @api.depends('check_in')
    def compute_check_in_time(self):
        for obj in self:
            obj.in_time = get_day_like_display(obj.check_in, self.env.user).strftime("%H:%M") if obj.check_in else ''
            

    # Гарсан цагийг тооцоолж хадгална.
    @api.depends('check_out')
    def compute_check_out_time(self):
        for obj in self:
            obj.out_time = get_day_like_display(obj.check_out, self.env.user).strftime("%H:%M") if obj.check_out else ''

    # Тухайн өдөр нь амралтын өдөр эсэхийг шалгана.
    def check_day_is_holiday(self, date):
        self.ensure_one()
        if date and ((date.weekday() == 0 and self.env.company.day_monday) or \
            (date.weekday() == 1 and self.env.company.day_tuesday) or \
            (date.weekday() == 2 and self.env.company.day_wednesday) or \
            (date.weekday() == 3 and self.env.company.day_thursday) or \
            (date.weekday() == 4 and self.env.company.day_friday) or \
            (date.weekday() == 5 and self.env.company.day_saturday) or \
            (date.weekday() == 6 and self.env.company.day_sunday)):
            return True
        else:
            return False

    # Нийт ирцийг цагаар тооцоолно.
    @api.depends('check_in', 'check_out')
    def compute_total_attendance_hours(self):
        for obj in self:
            if obj.check_in and obj.check_out:
                check_in = change_date_to_user_tz(obj.check_in, self.env.user)
                check_out = change_date_to_user_tz(obj.check_out, self.env.user)
                obj.total_attendance_hours = (check_out - check_in).total_seconds() / 3600
            else:
                obj.total_attendance_hours = 0

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrAttendance, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        root = etree.fromstring(res['arch'])
        if self._context.get('from_only_mine'):
            root.set('create', 'false',)
            root.set('edit', 'false', )
        else:
            root.set('create', 'true')
            root.set('edit', 'true', )
        res['arch'] = etree.tostring(root)
        return res

    def _set_attendace_hours(self):
        pass

    # Тухайн ирц үүсч буй сард гарсан ирц байхгүй бол л анхааруулга өгдөг байхаар дахин тодорхойлов.
    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Нэг ажилтны ирцийн бүртгэлийг хооронд нь шалгана.
            Нэг ажилтанд дараах байх ёстой:
                * хамгийн ихдээ 1ш "Нээлттэй" ирц (гарсан ирцгүй)
                * ажилтны өмнөх ирцүүдтэй давхацсан цагийн зааггүй байх
        """
        for attendance in self:
            # Бидэнд байгаа ирсэн цагаас өмнөх хамгийн сүүлийн ирцийг авч биднийхтэй давхцаж байгаа эсэхийг шалгана.
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_(
                    "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                                                     'empl_name': attendance.employee_id.name,
                                                     'datetime': fields.Datetime.to_string(
                                                         fields.Datetime.context_timestamp(self,fields.Datetime.from_string(attendance.check_in))),})

            if not attendance.check_out:
                tz = get_user_timezone(self.env.user)
                if attendance.check_in:
                    checkin_date = str(pytz.utc.localize(
                        datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S')).astimezone(tz).date())

                    # Хэрэв ирц нь "нээлттэй" (гарсан ирцгүй) байвал өөр "нээлттэй" ирц үлдээхгүй байхаар шалгана.
                    no_check_out_attendances = self.env['hr.attendance'].search([
                        ('employee_id', '=', attendance.employee_id.id),
                        ('check_out', '=', False),
                        ('id', '!=', attendance.id),
                    ], order='check_in desc', limit=1)
                    if no_check_out_attendances:
                        no_checkout_date = str(pytz.utc.localize(
                            datetime.strptime(str(no_check_out_attendances.check_in), '%Y-%m-%d %H:%M:%S')).astimezone(tz).date())
                        if no_checkout_date == checkin_date:
                            raise exceptions.ValidationError(_(
                            "Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                                                             'empl_name': attendance.employee_id.name,
                                                             'datetime': fields.Datetime.to_string(
                                                                 fields.Datetime.context_timestamp(self,fields.Datetime.from_string(no_check_out_attendances.check_in))),})
            else:
                # Гарсан цагаас өмнөх хамгийн сүүлийн ирсэн цагтай ирц нь урьд нь бидний тооцсон ирсэн цагийн өмнөхтэй ижил эсэхийг шалгана. Үгүй бол давхацсан байна.
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(_(
                        "Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                                                         'empl_name': attendance.employee_id.name,
                                                         'datetime': fields.Datetime.to_string(
                                                             fields.Datetime.context_timestamp(self,fields.Datetime.from_string(last_attendance_before_check_out.check_in))),})
