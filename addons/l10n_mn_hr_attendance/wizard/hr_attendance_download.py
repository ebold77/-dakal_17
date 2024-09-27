# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

import pytz
import time
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError
from odoo.addons.l10n_mn_hr_attendance.models.time_helper import *

_logger = logging.getLogger(__file__)


class HrAttendanceDownload(models.TransientModel):
    _name = "hr.attendance.download"
    _description = "Download employee attendances."

    # Системд 1ш ирцийн төхөөрөмж бүртгэлтэй байвал түүнийг автоматаар авна.
    @api.model
    def _default_device_ids(self):
        devices = self.env['hr.attendance.device'].search([])
        if len(devices) == 1:
            return devices.ids
        else:
            return False

    device_ids = fields.Many2many('hr.attendance.device', 'hr_attendance_download_device_rel', 'wizard_id', 'device_id', 'Devices', required=True, default=_default_device_ids)
    date_from = fields.Date('Date From', required=True, default = lambda *a: time.strftime('%Y-%m-1'))
    date_to = fields.Date('Date To', required=True, default = lambda *a: time.strftime('%Y-%m-%d'))
    employee_ids = fields.Many2many('hr.employee', 'hr_attendance_download_employee_rel', 'wizard_id', 'employee_id', 'Employees')

    # Ирц татна.
    def download_attendance(self, date_from, date_to, employees, devices):
        # Хэрэглэгчийн цагийн бүсийг авна.
        user_time_zone = pytz.UTC
        if self.env.user.tz:
            user_time_zone = pytz.timezone(self.env.user.tz)
        else:
            raise ValidationError(_('Warning!\n The user, who is downloading attendances need to set their time zone. You can set it on the user menu.'))
        _logger.info(_(u"User timezone: '%s'") % user_time_zone)

        # Ажилтнуудыг авна.
        if not employees:
            employees = self.env['hr.employee'].search([])

        # convert date to datetime
        date_from = datetime.strptime('%s 00:00:00' % str(date_from), DEFAULT_SERVER_DATETIME_FORMAT)
        date_to = datetime.strptime('%s 23:59:59' % str(date_to), DEFAULT_SERVER_DATETIME_FORMAT)
            
        all_device_attendances, all_identifies = [], []
        
        # Зурвасын талбарууд
        for device in devices:
            # Төхөөрөмжийн хэрэглэгч болон ирцийг авна.
            conn = device.get_connection()
            users = conn.get_users()

            user_ids = list(map(lambda x: x.user_id, users))
            _logger.info(_(u"Successfully downloaded users from '%s' device.") % device.name)
            attendances = conn.get_attendance()
            _logger.info(u"Successfully downloaded attendance from '%s' device." % device.name)
            device.close_connection(conn)

            # Төхөөрөмжийн цагийн бүсээр нутагшуулна.
            device_time_zone = pytz.timezone(device.tz)
            for att in attendances:
                att.timestamp = device_time_zone.localize(att.timestamp)
                att.status = device.name
                if att.user_id not in all_identifies:
                    all_identifies.append(att.user_id)

            # Хэрэглэгчийн цагийн бүс рүү хувиргана.
            for att in attendances:
                att.timestamp = att.timestamp.astimezone(user_time_zone).replace(tzinfo=None)

            # Ирцийг огноогоор шүүнэ.
            available_atts = list(filter(lambda x: x.timestamp >= date_from and x.timestamp <= date_to, attendances))
            
            # Бүх төхөөрөмжийн ирцийг нэг листэнд хадгална.
            all_device_attendances.extend(available_atts)

        if self._context.get('downloading_raw_attendance'):
            _logger.info(_(u"Started creating raw attendance to the database."))
            # Ирцийг үүсгэнэ.
            for employee in employees.filtered(lambda x: set(device.employee_device_id for device in x.attendance_device_ids) & set(all_identifies)):
                if employee.attendance_device_ids:
                    employee_device_ids = [device_id.employee_device_id for device_id in employee.attendance_device_ids]
                    for attendance in all_device_attendances:
                        if attendance.user_id in employee_device_ids:
                            attendance_date = get_display_day_to_user_day(attendance.timestamp, self.env.user).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            existen_raw_data = self.env['hr.attendance.raw.data'].search([('employee_id', '=', employee.id), ('date', '=', attendance_date)])
                            if not existen_raw_data:
                                self.env['hr.attendance.raw.data'].create({
                                    'employee_id': employee.id,
                                    'date': attendance_date,
                                    'device': attendance.status,
                                    'department_id': employee.department_id.sudo().id
                                })
                            elif existen_raw_data.department_id != employee.department_id:
                                existen_raw_data.write({'department_id': employee.department_id.id})
                                
            _logger.info(_(u'Finished creating raw attendance to the database.'))
        else:
            _logger.info(_(u'Started creating attendance to the database.'))
            # Ирцийг үүсгэнэ.
            for employee in employees.filtered(lambda x: set(device.employee_device_id for device in x.attendance_device_ids) & set(all_identifies)):
                available_atts = []
                
                if employee.attendance_device_ids:
                    employee_device_ids = [device_id.employee_device_id for device_id in employee.attendance_device_ids]
                    for attendance in all_device_attendances:
                        if attendance.user_id in employee_device_ids:
                            available_atts.append(attendance)
                    
                    available_atts.sort(key=lambda x: x.timestamp)
                    if available_atts:
                        self.create_employee_attendances(employee, available_atts, date_from, date_to)
            _logger.info(_(u'Finished creating attendance to the database.'))
        _logger.info('========================================')

    # Ирцийг автоматаар татах кроны функц.
    def auto_download_attendance(self):
        _logger.info('========================================')
        _logger.info(_(u'Started auto download attendance.'))
        employees = self.env['hr.employee'].search([])
        devices = self.env['hr.attendance.device'].search([('download_automatically', '=', True)])
        if not devices:
            _logger.info(_(u"There is no devices configured for auto download."))
        else:
            today = time.strftime('%Y-%m-%d')
            self.download_attendance((datetime.strptime(today, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'), today, employees, devices)

    # Ирц татуулна.
    def download(self):
        self.ensure_one()
        _logger.info('========================================')
        _logger.info(_(u'Started downloading attendance.'))

        self.download_attendance(self.date_from, self.date_to, self.employee_ids, self.device_ids)

    # Ирцийн төхөөрөмжийн нэрийг авна.
    def get_device_name(self, date, attendances, device_name=False):
        for att in attendances:
            if att.timestamp == date:
                device_name = att.status
        
        return device_name

    # Ажилтны ирцийг үүсгэнэ.
    def create_employee_attendances(self, employee, attendances, date_from_att=False, date_to_att=False):
        user_time_zone = pytz.timezone(self.env.user.tz)
        utc = pytz.UTC

        date = None
        day_attendance = self.env['hr.attendance']
        for att in attendances:
            if date != att.timestamp.date():
                date = att.timestamp.date()

                # Өдрийн ирцийг шалгана.
                existing_attendances = self.get_attendances_of_day(employee, date)
                if existing_attendances:
                    day_attendance = existing_attendances[0]
                    if len(existing_attendances) > 1:
                        (existing_attendances - day_attendance).unlink()

                att_in_utc = user_time_zone.localize(att.timestamp).astimezone(utc).replace(tzinfo=None)
                if existing_attendances and day_attendance:
                    # Төхөөрөмж дээрх ирц нь ERP дээрх ирцээс эрт
                    if day_attendance.check_in:
                        if att_in_utc < datetime.strptime(str(day_attendance.check_in), DEFAULT_SERVER_DATETIME_FORMAT):
                            day_attendance.check_in = att_in_utc
                    else:
                        day_attendance.check_in = att_in_utc
                else:
                    day_attendance = self.env['hr.attendance'].create({
                        'employee_id': employee.id,
                        'check_in': att_in_utc.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'check_out': (att_in_utc + timedelta(seconds=1)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'in_device_name': self.get_device_name(get_day_like_display(att_in_utc, self.env.user), attendances),
                        'company_id': employee.company_id.id,
                    })
            else:
                att_in_utc = user_time_zone.localize(att.timestamp).astimezone(utc).replace(tzinfo=None)
                # Төхөөрөмж дээрх ирц нь ERP дээрх ирцээс хойш
                if day_attendance.check_out:
                    if att_in_utc > datetime.strptime(str(day_attendance.check_out), DEFAULT_SERVER_DATETIME_FORMAT):
                        day_attendance.check_out = att_in_utc
                        day_attendance.out_device_name = self.get_device_name(get_day_like_display(att_in_utc, self.env.user), attendances)

    # Өдрийн ирцийг авна.
    def get_attendances_of_day(self, employee, date):
        user_time_zone = pytz.timezone(self.env.user.tz)
        utc = pytz.UTC
        from_dt = datetime.combine(date, datetime.min.time())
        to_dt = datetime.combine(date + timedelta(days=1), datetime.min.time())

        from_dt_str = user_time_zone.localize(from_dt).astimezone(utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        to_dt_str = (user_time_zone.localize(to_dt).astimezone(utc)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('check_in', '>=', from_dt_str), ('check_in', '<', to_dt_str)], order='check_in')

    # Түүхий ирцийг татна.
    def download_raw_attendance(self):
        self.ensure_one()
        _logger.info('========================================')
        _logger.info(_(u'Started downloading raw attendance.'))

        self.with_context({'downloading_raw_attendance': True}).download_attendance(self.date_from, self.date_to, self.employee_ids, self.device_ids)
