# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    attendance_device_ids = fields.One2many('hr.employee.attendance.device', 'employee_id', 'Attendance Device IDs', help="You can configure employee's ID on time attendance devices.")

    # Override. Ажилтан үүсгэхэд хэрэглэгч рүү write эрхийн алдаа гарч байсныг засав.
    def _inverse_manual_attendance(self):
        manual_attendance_group = self.env.ref('hr.group_hr_attendance')
        for employee in self:
            if employee.user_id:
                if employee.manual_attendance:
                    users = [(4, employee.user_id.id, 0)] # add
                else:
                    users = [(3, employee.user_id.id, 0)] # remove
                manual_attendance_group.sudo().write({'users': users})


class HrEmployeeAttendanceDevice(models.Model):
    _name = "hr.employee.attendance.device"
    _description = 'Employee Attendance Device IDs'

    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    employee_device_id = fields.Char('Employee Device ID', help="User ID on time attendance device for this employee.", required=True)
    device_id = fields.Many2one('hr.attendance.device', 'Attendance Device', ondelete='cascade')

    # Ажилтны төхөөрөмж дээрх дугааруудын утгыг хадгалахаас өмнө шалгана.
    @api.constrains('employee_id', 'employee_device_id', 'device_id')
    def check_fields(self):
        for employee_device in self:

            # Ажилтан дээр ирцийн төхөөрөмж сонгоогүй эсэхийг шалгана.
            if not employee_device.device_id:
                other_employee_device_ids_without_device = self.env['hr.employee.attendance.device'].search([
                    ('employee_id', '=', employee_device.employee_id.id),
                    ('id', '!=', employee_device.id)
                ])
                if other_employee_device_ids_without_device:
                    raise ValidationError(_("You can create only one attendance device ID without choosing device for employee: %s") % employee_device.employee_id.name)

            # Ажилтан нь тухайн төхөөрөмж дээр орсон эсэхийг шалгана.
            if employee_device.device_id:
                other_employee_device_ids_with_device = self.env['hr.employee.attendance.device'].search([
                    ('employee_id', '=', employee_device.employee_id.id),
                    ('device_id', '=', employee_device.device_id.id),
                    ('id', '!=', employee_device.id),
                    ('employee_device_id', '=', employee_device.employee_device_id)
                ])
                if other_employee_device_ids_with_device:
                    raise ValidationError(_("Device ID of %s device is already exists for employee: %s") % (employee_device.device_id.name, employee_device.employee_id.name))

                # Ажилтан дээр ирцийн төхөөрөмж сонгоогүй эсэхийг шалгана.
                existing_device_ids_without_device = self.env['hr.employee.attendance.device'].search([
                    ('employee_id', '=', employee_device.employee_id.id),
                    ('device_id', '=', False),
                    ('id', '!=', employee_device.id),
                    ('employee_device_id', '=', employee_device.employee_device_id)
                ])
                if existing_device_ids_without_device:
                    raise ValidationError(_("You can create only one attendance device ID without choosing device for employee: %s") % employee_device.employee_id.name)

            # Тухайн төхөөрөмжинд тухайн дугаараар 1 л ажилтанг бүртгэх боломжтой болгов.
            existing_device_ids = self.env['hr.employee.attendance.device'].search([
                ('employee_id', '!=', employee_device.employee_id.id),
                ('device_id', '=', employee_device.device_id.id),
                ('employee_device_id', '=', employee_device.employee_device_id),
                ('id', '!=', employee_device.id)
            ])
            if existing_device_ids:
                raise ValidationError(_("'%s' device number already registered for /%s/ employees !!!") % (employee_device.employee_device_id, ", ".join(existing_device_id.employee_id.name for existing_device_id in existing_device_ids)))