# -*- coding: utf-8 -*-
import time
import xlsxwriter
import base64
from datetime import datetime
from io import BytesIO

from odoo import fields, models, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

from odoo.addons.l10n_mn_web.models.time_helper import *
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles


class ProductLedgerReport(models.TransientModel):
    _name = "product.ledger.report"

    date_from = fields.Datetime('Start Date', required=True, default=lambda *a: time.strftime('%Y-01-01 16:00:00'))
    date_to = fields.Datetime('End Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d 15:59:59'))
    report_id = fields.Many2one('product.report', string='Product Report', required=True)
    report_view_type = fields.Selection([('qty', 'Quantity'),
                                         ('qty_cost', 'Quantity, Cost'),
                                         ('qty_price', 'Quantity, Price'),
                                         ('all', 'Quantity, Cost, Price')], string='Report View Type', default='qty_price')
    warehouse_group = fields.Boolean('Warehouse Group', default=False)
    show_barcode = fields.Boolean('Show Barcode', default=True)
    show_worthy_balance = fields.Boolean('Show Worthy Resources', default=False)
    show_qty_on_reserved = fields.Boolean('Show Quantity on Reserved', default=False)
    show_qty_on_hand = fields.Boolean("Show Quantity on Hand", default=False)
    show_current_cost = fields.Boolean('Show Current Cost', default=False)
    sort = fields.Selection([('name', 'Product Name'),
                             ('code', 'Default Code')], string='Sort', required=True, default='name')

    @api.model
    def default_get(self, default_fields):
        context = dict(self._context or {})
        res = super(ProductLedgerReport, self).default_get(default_fields)
        if context['active_model'] == 'product.report':
            report = self.env['product.report'].browse(context['active_id'])
            if 'report_id' in default_fields:
                res['report_id'] = report.id
            if 'report_view_type' in default_fields:
                res['report_view_type'] = report.report_view_type
            if 'warehouse_group' in default_fields and report.group_by == 'warehouse':
                res['warehouse_group'] = True
            if 'date_from' in default_fields:
                res['date_from'] = report.date_from
            if 'date_to' in default_fields:
                res['date_to'] = report.date_to
        return res

    def get_format(self, book):
        # create format
        return {'name': book.add_format(ReportExcelCellStyles.format_name),
                'filter': book.add_format(ReportExcelCellStyles.format_filter),
                'title': book.add_format(ReportExcelCellStyles.format_title),
                'content_text': book.add_format(ReportExcelCellStyles.format_content_text),
                'content_center': book.add_format(ReportExcelCellStyles.format_content_center),
                'content_float': book.add_format(ReportExcelCellStyles.format_content_float),
                'group_left': book.add_format(ReportExcelCellStyles.format_group_left),
                'group': book.add_format(ReportExcelCellStyles.format_group),
                'group_float': book.add_format(ReportExcelCellStyles.format_group_float),
                }

    def get_sheet(self, book, format, report_name):
        # create sheet
        sheet = book.add_worksheet(report_name)
        sheet.set_portrait()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.78, 0.39, 0.39, 0.39)  # 2cm, 1cm, 1cm, 1cm
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&C&"Times New Roman"&9&P', {'margin': 0.1})
        rowx = 1
        sheet, colx_number = self.get_column(sheet)
        # create company
        sheet.merge_range(rowx, 0, rowx, 2, '%s: %s' % (_('Company'), self.report_id.company_id and self.report_id.company_id.name or ''), format['filter'])
        rowx += 1
        sheet.merge_range(rowx, 0, rowx + 1, colx_number, report_name.upper(), format['name'])
        rowx += 2
        # create duration
        sheet.merge_range(rowx, 0, rowx, 3, '%s: %s - %s' % (_('Duration'), self.date_from, self.date_to), format['filter'])
        rowx += 1
        # create date
        sheet.merge_range(rowx, 0, rowx, 2, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format['filter'])
        rowx += 2
        return sheet, rowx

    def get_column(self, sheet):
        # compute column
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 13)
        if self.show_barcode:
            sheet.set_column('C:C', 13)
            sheet.set_column('D:D', 40)
            sheet.set_column('E:E', 10)
            sheet.set_column('F:AD', 15)
        else:
            sheet.set_column('C:C', 30)
            sheet.set_column('D:D', 10)
            sheet.set_column('E:AD', 15)
        return sheet, 7

    def get_header(self, sheet, rowx, format_title):
        # Товчоо тайлангийн хүснэгтийн толгой зурах
        colx = col = 0
        sheet.merge_range(rowx, col, rowx + 1, col, _('Seq'), format_title)
        col += 1
        sheet.merge_range(rowx, col, rowx + 1, col, _('Default Code'), format_title)
        if self.show_barcode:
            col += 1
            sheet.merge_range(rowx, col, rowx + 1, col, _('Barcode'), format_title)
        col += 1
        sheet.merge_range(rowx, col, rowx + 1, col, _('Product Name'), format_title)
        col += 1
        sheet.merge_range(rowx, col, rowx + 1, col, _('Product UoM'), format_title)
        col += 1
        if self.report_view_type == 'qty_price':
            # Тоо хэмжээ, Үнэ
            colx += 1
            sheet.write(rowx + 1, col + 1, _('Total Price'), format_title)
            sheet.write(rowx + 1, col + 3, _('Total Price'), format_title)
            sheet.write(rowx + 1, col + 5, _('Total Price'), format_title)
            sheet.write(rowx + 1, col + 7, _('Total Price'), format_title)
        elif self.report_view_type == 'qty_cost':
            # Тоо хэмжээ, Өртөг
            colx += 1
            sheet.write(rowx + 1, col + 1, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 3, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 5, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 8, _('Total Cost'), format_title)
        elif self.report_view_type == 'all':
            # Бүгд
            colx += 2
            sheet.write(rowx + 1, col + 1, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 2, _('Total Price'), format_title)
            sheet.write(rowx + 1, col + 4, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 5, _('Total Price'), format_title)
            sheet.write(rowx + 1, col + 7, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 8, _('Total Price'), format_title)
            sheet.write(rowx + 1, col + 11, _('Total Cost'), format_title)
            sheet.write(rowx + 1, col + 12, _('Total Price'), format_title)
        sheet.merge_range(rowx, col, rowx, col + colx, _('Initial Balance'), format_title)
        sheet.write(rowx + 1, col, _('Quantity'), format_title)
        col += colx + 1
        sheet.merge_range(rowx, col, rowx, col + colx, _('Income'), format_title)
        sheet.write(rowx + 1, col, _('Quantity'), format_title)
        col += colx + 1
        sheet.merge_range(rowx, col, rowx, col + colx, _('Expense'), format_title)
        sheet.write(rowx + 1, col, _('Quantity'), format_title)
        col += colx + 1
        if self.report_view_type in ('qty_cost', 'all'):
            # Тоо хэмжээ, Өртөг эсвэл Бүгд
            sheet.write(rowx + 1, col, _('Cost'), format_title)
            colx += 1
        sheet.merge_range(rowx, col, rowx, col + colx, _('End Balance'), format_title)
        sheet.write(rowx + 1, col + 1 if self.report_view_type in ('qty_cost', 'all') else col, _('Quantity'), format_title)
        if self.report_view_type == 'qty':
            sheet.write(rowx, col - 3, _('Initial Balance'), format_title)
            sheet.write(rowx, col - 2, _('Income'), format_title)
            sheet.write(rowx, col - 1, _('Expense'), format_title)
            sheet.write(rowx, col, _('End Balance'), format_title)
        col += colx + 1
        if self.show_worthy_balance:
            # Барааны зохистой нөөц харуулах
            sheet.merge_range(rowx, col, rowx + 1, col, _('Worthy Balance'), format_title)
            col += 1
            sheet.merge_range(rowx, col, rowx + 1, col, _('Worthy Balance Difference'), format_title)
            col += 1
        if self.show_qty_on_reserved:
            # Нөөцөлсөн тоо хэмжээг харуулах
            sheet.merge_range(rowx, col, rowx + 1, col, _('Quantity on Reserved'), format_title)
            col += 1
            sheet.merge_range(rowx, col, rowx + 1, col, _('Quantity on Available'), format_title)
            col += 1
        if self.show_qty_on_hand:
            # Гарт байгаа тоо хэмжээг харуулах
            sheet.merge_range(rowx, col, rowx + 1, col, _('Quantity on Hand'), format_title)
            col += 1
            sheet.merge_range(rowx, col, rowx + 1, col, _('Quantity on Hand Difference'), format_title)
            col += 1
        if self.show_current_cost and self.report_view_type in ('qty_cost', 'all'):
            # Одоогийн өртөг харуулах
            sheet.merge_range(rowx, col, rowx + 1, col, _('Current Cost'), format_title)
            col += 1
            sheet.merge_range(rowx, col, rowx + 1, col, _('Current Cost Difference'), format_title)
            col += 1
        rowx += 2
        return sheet, rowx

    def get_line(self):
        # Эхлэл болон тухайн хугацааны хоорондох утгыг олох
        show_field = {'show_barcode': self.show_barcode,
                      'show_worthy_balance': self.show_worthy_balance,
                      'show_current_cost': self.show_current_cost,
                      'show_qty_on_hand': self.show_qty_on_hand,
                      'show_qty_on_reserved': self.show_qty_on_reserved,
                      }
        date_field = {'date_from': self.date_from,
                      'date_to': self.date_to,
                      }
        lines = self.report_id.with_context(show_field=show_field, date_field=date_field, sort=self.sort).get_query(True)
        return lines

    def get_text_value(self, sheet, rowx, format, line, sequence, name, is_group):
        # Тайлангийн бүлэглэлт болон мөрийн текст утгыг зурах
        col = colx = 0
        if self.show_barcode:
            col += 1
        if is_group:
            if sequence:
                sheet.write(rowx, 0, sequence, format['group'])
                colx = 1
            sheet.merge_range(rowx, colx, rowx, col + 3, name, format['group_left'] if sequence else format['group'])
        else:
            if self.show_barcode:
                sheet.write(rowx, 2, line['barcode'], format['content_center'])
            sheet.write(rowx, 0, sequence, format['content_center'])
            sheet.write(rowx, 1, line['code'], format['content_center'])
            sheet.write(rowx, col + 2, name, format['content_text'])
            sheet.write(rowx, col + 3, line['uom_name'], format['content_center'])
        return sheet, col + 3, rowx

    def get_value(self, sheet, rowx, col, format, line, is_group):
        # Тайлангийн мөрийн тоон утгыг зурах
        cost = 0
        colx = 0
        format_float = format['content_float']
        if is_group:
            format_float = format['group_float']
        end_qty = line['initial_qty'] + line['income_qty'] - line['expense_qty']
        col += 1
        if self.report_view_type == 'qty_price':
            # Тоо хэмжээ, Үнэ
            end_price = line['initial_price'] + line['income_price'] - line['expense_price']
            colx += 1
            sheet.write(rowx, col + 1, line['initial_price'] or 0, format_float)
            sheet.write(rowx, col + 3, line['income_price'] or 0, format_float)
            sheet.write(rowx, col + 5, line['expense_price'] or 0, format_float)
            sheet.write(rowx, col + 7, end_price or 0, format_float)
        elif self.report_view_type == 'qty_cost':
            # Тоо хэмжээ, Өртөг
            end_cost = line['initial_cost'] + line['income_cost'] - line['expense_cost']
            colx += 1
            sheet.write(rowx, col + 1, line['initial_cost'] or 0, format_float)
            sheet.write(rowx, col + 3, line['income_cost'] or 0, format_float)
            sheet.write(rowx, col + 5, line['expense_cost'] or 0, format_float)
            sheet.write(rowx, col + 8, end_cost or 0, format_float)
        elif self.report_view_type == 'all':
            # Бүгд
            end_cost = line['initial_cost'] + line['income_cost'] - line['expense_cost']
            end_price = line['initial_price'] + line['income_price'] - line['expense_price']
            colx += 2
            sheet.write(rowx, col + 1, line['initial_cost'] or 0, format_float)
            sheet.write(rowx, col + 2, line['initial_price'] or 0, format_float)
            sheet.write(rowx, col + 4, line['income_cost'] or 0, format_float)
            sheet.write(rowx, col + 5, line['income_price'] or 0, format_float)
            sheet.write(rowx, col + 7, line['expense_cost'] or 0, format_float)
            sheet.write(rowx, col + 8, line['expense_price'] or 0, format_float)
            sheet.write(rowx, col + 11, end_cost or 0, format_float)
            sheet.write(rowx, col + 12, end_price or 0, format_float)
        sheet.write(rowx, col, line['initial_qty'] or 0, format_float)
        col += colx + 1
        sheet.write(rowx, col, line['income_qty'] or 0, format_float)
        col += colx + 1
        sheet.write(rowx, col, line['expense_qty'] or 0, format_float)
        col += colx + 1
        if self.report_view_type in ('qty_cost', 'all'):
            # Тоо хэмжээ, Өртөг эсвэл Бүгд
            cost = end_cost / end_qty if end_qty > 0 else 0
            sheet.write(rowx, col, '' if is_group else cost, format_float)
            col += 1
        sheet.write(rowx, col, end_qty or 0, format_float)
        col += colx + 1
        if self.show_worthy_balance:
            # Барааны зохистой нөөц харуулах
            sheet.write(rowx, col, '' if is_group else (line['worthy_balance'] or 0), format_float)
            col += 1
            sheet.write(rowx, col, '' if is_group else (end_qty - line['worthy_balance'] or 0), format_float)
            col += 1
        if self.show_qty_on_reserved:
            # Нөөцөлсөн тоо хэмжээг харуулах
            sheet.write(rowx, col, '' if is_group else (line['qty_on_reserved'] or 0), format_float)
            col += 1
            sheet.write(rowx, col, '' if is_group else (end_qty - line['qty_on_reserved'] or 0), format_float)
            col += 1
        if self.show_qty_on_hand:
            # Гарт байгаа тоо хэмжээг харуулах
            sheet.write(rowx, col, '' if is_group else (line['qty_on_hand'] or 0), format_float)
            col += 1
            sheet.write(rowx, col, '' if is_group else (end_qty - line['qty_on_hand'] or 0), format_float)
            col += 1
        if self.show_current_cost and self.report_view_type in ('qty_cost', 'all'):
            # Одоогийн өртөг харуулах
            sheet.write(rowx, col, '' if is_group else (line['current_cost'] or 0), format_float)
            col += 1
            sheet.write(rowx, col, '' if is_group else (cost - line['current_cost'] or 0), format_float)
            col += 1
        return sheet

    def get_footer(self, sheet, report_excel_output_obj, rowx, format):
        # create footer
        sheet.merge_range(rowx, 1, rowx, 5, '%s: ........................................... ( %s )'
                          % (_('Executive Director'), report_excel_output_obj.get_emp_name_from_sign('ceo', self.report_id.company_id)), format['filter'])
        rowx += 1
        sheet.merge_range(rowx, 1, rowx, 5, '%s: ........................................... ( %s )'
                          % (_('General Accountant'), report_excel_output_obj.get_emp_name_from_sign('general_account', self.report_id.company_id)), format['filter'])

    def export_report(self):
        # Бараа материалын товчоо тайлан тайлан
        # create workbook
        output = BytesIO()
        book = xlsxwriter.Workbook(output)
        # create name
        report_name = _('Product Ledger Report')
        file_name = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'),)
        # create formats
        format = self.get_format(book)
        # create report object
        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=('product_ledger_report'), form_title=file_name).create({})
        # create sheet
        sheet, rowx = self.get_sheet(book, format, report_name)
        # create header
        sheet, rowx = self.get_header(sheet, rowx, format['title'])
        lines = self.get_line()
        report = self.report_id
        group = group_id = False  # Бүлэглэлт 1
        group2 = group2_id = False  # Бүлэглэлт 2
        total = report._reset_dict()
        group_total = report._reset_dict()
        group2_total = report._reset_dict()
        seq = group_seq = group2_seq = 1
        # БМ-н товчоо тайлангийн мөрийг зурах
        for line in lines:
            sequence = _('%s') % seq
            if report.group_by != 'no_group':
                group_id = line['group_id']
                group_name = line['group_name']
                if not group or group != group_id:
                    # Бүлэглэлт 1
                    level = 1
                    if group:
                        sheet = self.get_value(sheet, rowg, col, format, group_total, True)
                        group_total = report._reset_dict()
                        group_seq += 1
                        group2_seq = 0
                        seq = 1
                    sheet, col, rowg = self.get_text_value(sheet, rowx, format, line, _('%s') % group_seq, group_name, True)
                    sheet.set_row(rowx, None, None, {'hidden': 0, 'level': level})
                    rowx += 1
                sequence = _('%s.%s') % (group_seq, seq)
            if report.group_by == 'warehouse' and report.group2_by != 'no_group':
                group2_id = line['group2_id']
                group2_name = line['group2_name']
                if not group2 or group2 != group2_id or group != group_id:
                    level = 2
                    # Бүлэглэлт 2
                    if group2:
                        sheet = self.get_value(sheet, rows, col, format, group2_total, True)
                        group2_total = report._reset_dict()
                        group2_seq += 1
                        seq = 1
                    sheet, col, rows = self.get_text_value(sheet, rowx, format, line, _('%s.%s') % (group_seq, group2_seq), group2_name, True)
                    sheet.set_row(rowx, None, None, {'hidden': 0, 'level': level})
                    rowx += 1
                sequence = _('%s.%s.%s') % (group_seq, group2_seq, seq)
            # Тайлангийн үндсэн мөрийг зурах
            if line['prod_id'] != 0:
                name = line['name']
                # Ирээдүйд сайжруулах -- Удаан ажиллаж магадгүй
                variant = self.env['product.product'].browse(line['prod_id']).product_template_attribute_value_ids._get_combination_name()
                if variant:
                    name = variant and "%s (%s)" % (line['name'], variant)
                sheet, col, rowx = self.get_text_value(sheet, rowx, format, line, sequence, name, False)
                sheet = self.get_value(sheet, rowx, col, format, line, False)
                sheet.set_row(rowx, None, None, {'hidden': 0, 'level': level + 1})
                rowx += 1
                seq += 1
            # Нийт дүнг тооцоолох
            report.get_total(total, line)
            # Бүлэглэлтийн дэд дүнг тооцоолох
            report.get_total(group_total, line)
            # Бүлэглэлт 2-н дэд дүнг тооцоолох
            report.get_total(group2_total, line)
            if report.group_by != 'no_group':
                group = line['group_id']
            if report.group_by == 'warehouse' and report.group2_by != 'no_group':
                group2 = line['group2_id']
        if group:
            # Бүлэглэлт
            sheet = self.get_value(sheet, rowg, col, format, group_total, True)
        if report.group_by == 'warehouse' and group2:
            # Борлуулалтын ажилтны бүлэглэлт
            sheet = self.get_value(sheet, rows, col, format, group2_total, True)
        # Нийт дүн
        sheet, col, rows = self.get_text_value(sheet, rowx, format, False, '', _('TOTAL'), True)
        sheet = self.get_value(sheet, rowx, col, format, total, True)
        rowx += 2
        # create footer
        self.get_footer(sheet, report_excel_output_obj, rowx, format)
        book.close()
        # set file dat
        report_excel_output_obj.filedata = base64.b64encode(output.getvalue())
        # call export function
        return report_excel_output_obj.export_report()