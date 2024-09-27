# -*- coding: utf-8 -*-

import base64
from io import BytesIO
from lxml import etree
import time
from datetime import datetime, timedelta
import xlsxwriter

from odoo import models, fields, api, _
from odoo.addons.l10n_mn_report.models.report_helper import *
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles
from odoo.addons.l10n_mn_hr_attendance.models.time_helper import *
from odoo.exceptions import AccessError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class HRAttendanceReport(models.TransientModel):
    """
        ИРЦИЙН ДЭЛГЭРЭНГҮЙ ТАЙЛАН
    """
    _name = 'hr.attendance.report'
    _description = "HR Attendance Report"

    # Нэвтэрсэн хэрэглэгчийн холбоотой ажилтанг тайланд автоматаар нэмнэ.
    @api.model
    def get_default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, ondelete='cascade', default=lambda self: self.env.company.id)
    date_from = fields.Date('Date From', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    employee_ids = fields.Many2many('hr.employee', 'hr_attendance_report_employee_rel', 'wizard_id', 'employee_id', string='Employee', required=True, ondelete='cascade', default=get_default_employee)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HRAttendanceReport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])

            # Хэрэглэгчийн эрхээс хамааруулсан домайн.
            if self.env.user.has_group('hr.group_hr_manager'):
                domain = "[]"
            elif self.env.user.has_group('hr.group_hr_user'):
                domain = "['|', '|', ('parent_id.user_id', '=', %s), ('user_id', '=', %s), ('department_id', 'in', %s)]" % (self.env.uid, self.env.uid, self.env.user.allowed_department_ids.ids or [])
            else:
                domain = "[('user_id', '=', %s)]" % self.env.uid
            for node in doc.xpath("//field[@name='employee_ids']"):
                node.set('domain', domain)

            res['arch'] = etree.tostring(doc)
        return res

    # Өдрийн гаригыг орчуулагдах боломжтой болгов.
    def get_week_str(self, date):
        week_str = date.strftime("%a")
        if week_str == 'Mon':
            week_str = _('Mon')
        elif week_str == 'Tue':
            week_str = _('Tue')
        elif week_str == 'Wed':
            week_str = _('Wed')
        elif week_str == 'Thu':
            week_str = _('Thu')
        elif week_str == 'Fri':
            week_str = _('Fri')
        elif week_str == 'Sat':
            week_str = _('Sat')
        elif week_str == 'Sun':
            week_str = _('Sun')
        return week_str

    # Амралтын өдөр эсэхийг тодорхойлно.
    def get_day_is_weekend(self, date):
        day_str = self.get_week_str(date)
        if day_str == 'Sun' or day_str == 'Sat' or day_str == 'Бя' or day_str == 'Ня':
            return True
        return False

    # Амралт, чөлөөний төрлийг орчуулагдах боломжтой болгов.
    def get_holiday_type(self, type):
        if type == 'paid':
            type = _('p/hol')
        elif type == 'unpaid':
            type = _('u.p/hol')
        elif type == 'annual_leave':
            type = _('a.l/hol')
        elif type == 'sick_leave':
            type = _('s.l/hol')
        return type

    # Sheet-ийн форматыг онооно.
    def get_sheet_format(self, sheet):
        sheet.set_portrait()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.39, 0.39, 0.39, 0.39)  # 1cm, 1cm, 1cm, 1cm
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&C&"Times New Roman"&9&P', {'margin': 0.1})
        sheet.hide_gridlines(2)
        sheet.set_zoom(60)
        return sheet

    # Толгойг онооно.
    def get_header(self, sheet, header_formats, rowx, report_name):
        sheet.merge_range(rowx, 0, rowx, 4, '%s: %s' % (_('Company name'), self.company_id.name), header_formats['format_filter'])
        rowx += 2
        sheet.merge_range(rowx, 0, rowx, 14, report_name.upper(), header_formats['format_name'])
        rowx += 2
        sheet.merge_range(rowx, 0, rowx, 4, '%s: %s - %s' % (_('Duration'), self.date_from, self.date_to), header_formats['format_filter'])
        rowx += 1
        sheet.merge_range(rowx, 0, rowx, 4, '%s: %s' % (_('Create Date'), get_day_like_display(fields.Datetime.now(), self.env.user)), header_formats['format_filter'])
        rowx += 1

        return sheet, rowx

    # Агуулгын толгойг онооно.
    def get_content_value_header(self, sheet, rowx, content_formats):

        # create content header
        sheet.merge_range(rowx, 0, rowx + 1, 0, _('№'), content_formats['format_group'])
        sheet.merge_range(rowx, 1, rowx + 1, 1, _('Attendance code'), content_formats['format_group'])
        sheet.merge_range(rowx, 2, rowx + 1, 2, _('Last name'), content_formats['format_group'])
        sheet.merge_range(rowx, 3, rowx + 1, 3, _('Name'), content_formats['format_group'])
        sheet.merge_range(rowx, 4, rowx + 1, 4, _('Job'), content_formats['format_group'])
        sheet.merge_range(rowx, 5, rowx + 1, 5, _('Department'), content_formats['format_group'])
        sheet.set_row(rowx, 25)
        sheet.set_row(rowx + 1, 25)

        # Агуулгын динамик толгойг онооно.
        date_start = datetime.strptime(str(self.date_from), DEFAULT_SERVER_DATE_FORMAT)
        date_end = datetime.strptime(str(self.date_to), DEFAULT_SERVER_DATE_FORMAT)
        colm, col, sequence = 6, 6, 1
        att_month = date_start.month
        while date_start <= date_end:
            if att_month == date_start.month:
                if colm == col:
                    sheet.write(rowx, col, '%s %s' % (att_month, _('Month')), content_formats['format_group'])
                else:
                    sheet.merge_range(rowx, colm, rowx, col, '%s %s' %(att_month, _('Month')), content_formats['format_group'])
            else:
                att_month = date_start.month
                colm = col
            sheet.write(rowx + 1, col, '%s.%s' % (date_start.day, self.get_week_str(date_start)), content_formats['format_group'])
            date_start = date_start + timedelta(days=1)
            col+=1
        rowx += 2

        return sheet, rowx

    # Тайлангийн өгөгдлийг онооно.
    def get_value(self, sheet, rowx, content_formats):
        date_end = datetime.strptime(str(self.date_to), DEFAULT_SERVER_DATE_FORMAT)
        sequence = 1
        weekend_day = _('we/day')
        absent = _('Abs')
        uncompleted = _('half/att')
        out_work = _('out/work')

        for employee in self.employee_ids:
            col_att = 6
            date_start = datetime.strptime(str(self.date_from), DEFAULT_SERVER_DATE_FORMAT)
            identities = employee.mapped('attendance_device_ids').mapped('employee_device_id') or []

            sheet.write(rowx, 0, sequence, content_formats['format_content_center'])
            sheet.write(rowx, 1, ", ".join(str(identity) for identity in identities) or "", content_formats['format_content_center'])
            sheet.write(rowx, 2, "", content_formats['format_content_text'])
            sheet.write(rowx, 3, employee.name, content_formats['format_content_text'])
            sheet.write(rowx, 4, employee.job_id.name or "", content_formats['format_content_text'])
            sheet.write(rowx, 5, employee.department_id.name or "", content_formats['format_content_text'])

            while date_start <= date_end:
                is_weekend = self.get_day_is_weekend(date_start)
                date_from = str(get_display_day_to_user_day(date_start.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' 00:00:00', self.env.user))
                date_to = str(get_display_day_to_user_day(date_start.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' 23:59:59', self.env.user))

                domain = [('employee_id', '=', employee.id)]
                domain.extend(get_duplicated_day_domain('check_in', 'check_out', date_from, date_to, self.env.user))
                att_id = self.env['hr.attendance'].search(domain, limit=1)

                balance_types, holiday_status = False, ""
                if self.env.get('hr.holidays', False) != False:
                    domain = [('employee_id', '=', employee.id), ('state', '=', 'validate'), ('date_from', '!=', False), ('date_to', '!=', False)]
                    domain.extend(get_duplicated_day_domain('date_from', 'date_to', date_from, date_to, self.env.user))
                    balance_types = list(set(self.env['hr.holidays'].search(domain).mapped('holiday_status_id').mapped('balance_type')))
                    holiday_status = '\n'.join('%s' % self.get_holiday_type(balance_type) for balance_type in balance_types)

                event_ids = False
                if self.env.get('calendar.event', False) != False and hasattr(self.env.get('calendar.event'), 'is_outside_work'):
                    partner_id = employee.address_home_id or (employee.user_id.sudo().partner_id if employee.user_id and employee.user_id.sudo().partner_id else False)
                    if partner_id:
                        domain = [('company_id', '=', employee.company_id.id), ('is_outside_work', '=', True), ('partner_ids', 'in', partner_id.id)]
                        domain.extend(get_duplicated_day_domain('start', 'stop', date_from, date_to, self.env.user))
                        if hasattr(employee.company_id, 'require_cnfrmtn_on_outwork') and employee.company_id.require_cnfrmtn_on_outwork:
                            domain.append(('state', '=', 'open'))
                        event_ids = self.env['calendar.event'].search(domain)

                value, format = '', content_formats['format_content_center']
                if not att_id:
                    if balance_types:
                        value, format = '%s' % holiday_status, content_formats['format_blue_text']
                    if event_ids:
                        value += ('%s' % out_work if not value else '\n%s' % out_work)
                        format = content_formats['format_blue_text']
                    if is_weekend:
                        value += ('%s' % weekend_day if not value else '\n%s' % weekend_day)
                        format = content_formats['format_black_text_greyed_out']
                    if not (is_weekend or balance_types or event_ids):
                        value, format = '%s' % absent, content_formats['format_red_text']
                else:
                    check_in_hour = get_day_like_display(att_id.check_in, self.env.user).strftime('%H:%M') if att_id.check_in else False
                    check_out_hour = get_day_like_display(att_id.check_out, self.env.user).strftime('%H:%M') if att_id.check_out else False

                    if check_in_hour and check_out_hour:
                        value = "%s\n%s" % (check_in_hour, check_out_hour)
                        format = content_formats['format_black_text']
                        if balance_types:
                            value += '\n%s' % holiday_status
                            format = content_formats['format_blue_text']
                        if event_ids:
                            value += '\n%s' % out_work
                            format = content_formats['format_blue_text']
                        if is_weekend:
                            value += '\n%s' % weekend_day
                            format = content_formats['format_green_text_greyed_out']
                    else:
                        value = "%s" % (check_in_hour or check_out_hour)
                        format = content_formats['format_red_text']
                        if balance_types:
                            value += '\n%s' % holiday_status
                        if event_ids:
                            value += '\n%s' % out_work
                        value += "\n%s" % uncompleted

                sheet.write(rowx, col_att, value, format)

                col_att +=1
                date_start += timedelta(days=1)

            sequence += 1
            sheet.set_row(rowx, 30)
            rowx +=1

        return sheet, rowx

    # Тайланг экспортлоно.
    def export_report(self):
        # Workbook-г үүсгэнэ.
        output = BytesIO()
        book = xlsxwriter.Workbook(output)

        # Нэр онооно.
        report_name = _('HR Attendance Detail Report')
        file_name = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'),)

        # Форматыг онооно.
        format_name = book.add_format(ReportExcelCellStyles.format_name)
        format_filter = book.add_format(ReportExcelCellStyles.format_filter)
        format_group = book.add_format(ReportExcelCellStyles.format_content_header)
        format_content_text = book.add_format(ReportExcelCellStyles.format_content_text)
        format_content_center = book.add_format(ReportExcelCellStyles.format_content_center)
        format_red_text = book.add_format(ReportExcelCellStyles.format_content_center_red_text)
        format_blue_text = book.add_format(ReportExcelCellStyles.format_content_center_blue_text)
        format_green_text_greyed_out = book.add_format(ReportExcelCellStyles.format_content_center_green_text_greyed_out)
        format_black_text = book.add_format(ReportExcelCellStyles.format_content_center_float)
        format_black_text_greyed_out = book.add_format(ReportExcelCellStyles.format_content_center_float_greyed_out)

        header_formats = {
            'format_filter': format_filter,
            'format_name': format_name,
        }

        content_formats = {
            'format_group': format_group,
            'format_content_center': format_content_center,
            'format_content_text': format_content_text,
            'format_red_text': format_red_text,
            'format_blue_text': format_blue_text,
            'format_black_text': format_black_text,
            'format_black_text_greyed_out': format_black_text_greyed_out,
            'format_green_text_greyed_out': format_green_text_greyed_out,
        }

        # Тайлангийн object-ийг үүсгэнэ.
        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=('hr_attendance_detail_report'), form_title=file_name).create({})

        # Sheet үүсгэнэ.
        sheet = book.add_worksheet(report_name)
        sheet = self.get_sheet_format(sheet)

        # Багануудыг тооцоолно.
        sheet.set_column('A:A', 3)
        sheet.set_column('B:B', 8)
        sheet.set_column('C:D', 13)
        sheet.set_column('E:F', 20)

        # Толгойг онооно.
        rowx = 0
        sheet, rowx = self.get_header(sheet, header_formats, rowx, report_name)

        # Агуулгыг онооно.
        sheet, rowx = self.get_content_value_header(sheet, rowx, content_formats)
        sheet, rowx = self.get_value(sheet, rowx, content_formats)

        # Workbook-ийг хааж, тайланг экспортлоно.
        book.close()
        report_excel_output_obj.filedata = base64.b64encode(output.getvalue())
        return report_excel_output_obj.export_report()
