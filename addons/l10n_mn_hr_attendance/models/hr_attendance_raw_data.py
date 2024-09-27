# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class HrAttendanceRawData(models.Model):
    _name = "hr.attendance.raw.data"
    _description = "HR Attendance Raw Data"

    employee_id = fields.Many2one('hr.employee', required=False, string='Employee')
    identification_id = fields.Char(related='employee_id.identification_id', store=True, readonly=False, string='Identification No') # Импортлохын тулд readonly=False байх хэрэгтэй
    date = fields.Datetime(required=True, string='Date')
    device = fields.Char(string='Attendance Device')
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True, readonly=True)

    # Түүхий ирцийг үүсгэнэ.
    @api.model
    def create(self, vals):
        if self._context.get('import_file') and not self.env.user.has_group('l10n_mn_hr_attendance.group_hr_attendance_advanced'):
            raise AccessError(_("If you want to import, you must have 'Attendance/Advanced Configuration' right !!!"))
        if self._context.get('from_menu') and not self._context.get('import_file'):
            raise AccessError(_("Cannot create raw attendance, but if you have 'Attendance/Advanced Configuration' right, you can import it !!!"))
        if 'identification_id' in vals.keys() and not 'employee_id' in vals.keys():
            employee_id = self.env['hr.employee'].search([('identification_id', '=', vals['identification_id'])])
            if employee_id:
                vals['employee_id'] = employee_id.id
        return super(HrAttendanceRawData, self).create(vals)

    # Түүхий ирцийг устгана.
    def unlink(self):
        if not self.env.user.has_group('l10n_mn_hr_attendance.group_hr_attendance_advanced'):
            raise AccessError(_("If you want to delete, you must have 'Attendance/Advanced Configuration' right !!!"))
        return super(HrAttendanceRawData, self).unlink()
