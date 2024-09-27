# -*- coding: utf-8 -*-
from io import BytesIO
import base64
import time
import datetime
import xlsxwriter
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles

from odoo import api, fields, models, _
from odoo.tools import date_utils

import logging
logger = logging.getLogger(__name__)

class ReportPosSession(models.TransientModel):

    _name = 'report.pos.session'
    _description = 'Generate XLSX report for Pos session'

    

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    start_date = fields.Date('Start Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    end_date = fields.Date('End Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    config_ids = fields.Many2many('pos.config', 'pos_session_report_rel','wizard_id', 'config_id', 'Pos Config')
   

    def export_report_xls(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        # report_obj = self.env['account.financial.report']
        # create name
        report_name = _('Pos session report')
        file_name = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'),)
        comp = self.env.user.company_id.name

        # create formats
        format_name = workbook.add_format(ReportExcelCellStyles.format_name)
        format_filter = workbook.add_format(ReportExcelCellStyles.format_filter)
        format_title = workbook.add_format(ReportExcelCellStyles.format_title)
        format_title_small = workbook.add_format(ReportExcelCellStyles.format_title_small)
        format_content_text = workbook.add_format(ReportExcelCellStyles.format_content_text)
        format_content_float = workbook.add_format(ReportExcelCellStyles.format_content_float)
        format_content_bold_text = workbook.add_format(ReportExcelCellStyles.format_content_bold_left)
        format_content_bold_float = workbook.add_format(ReportExcelCellStyles.format_content_bold_float)

        # create report object
        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=('pos_sesion_report'), form_title=file_name, date_to=self.end_date, date_from=self.start_date).create({})

        # create sheet
        sheet = workbook.add_worksheet(report_name)
        sheet.set_portrait()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.78, 0.39, 0.39, 0.39)  # 2cm, 1cm, 1cm, 1cm
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&C&"Times New Roman"&9&P', {'margin': 0.1})
        rowx = 1

        sheet.merge_range(0, 1, 0, 6, u'Байгууллагын нэр: %s' %comp, format_filter)
        sheet.merge_range(1, 1, 1, 6, u'Посын Орлогын тайлан', format_name)
        
        
        sheet.merge_range(2, 5, 2,6, u'Хэвлэсэн: %s' %datetime.datetime.now().strftime("%Y-%m-%d"), format_filter)
        
        row = 4
        sheet.set_column(0, 0, 2)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        
        sheet.set_row(4, 30)
        for config_id in self.config_ids:
            sheet.write(row, 0, u'№', format_title)
            sheet.write(row, 1, u'Огноо', format_title)
            sheet.write(row, 2, u'Сэшн', format_title)
            sheet.write(row, 3, u'Нийт борлуулалт', format_title)
            sheet.write(row, 4, u'Буцаалт', format_title)
            col = 5
            for payment_method in config_id.payment_method_ids:
                sheet.write(row, col, payment_method.name, format_title)
                sheet.set_column(col, col, 15)
                col += 1
            sheet.merge_range(row+1, 0, row+1, col-1, u'%s' %config_id.name, format_title_small)
            row +=1
            session_ids = self.env['pos.session'].search([('config_id','=', config_id.id), 
                ('start_at','>=', self.start_date), ('start_at','<=', self.end_date)])
            sum_return = 0
            sum_total_payment = 0
            sum_total = {}
            sum_total_list = []
            j = 1
            for session in session_ids.sorted(key=lambda x: x.start_at):
                total_payment = total_payment_method= 0
                total_return = 0
                result = self.env['pos.payment'].read_group([('session_id', '=', session.id)], ['amount'], ['session_id'])
                if result:
                    total_payment = result[0]['amount']
         
                result2 = self.env['pos.order'].read_group([('session_id', '=', session.id),('amount_paid','<',0)], ['amount_paid'], ['session_id'])
                if result2:
                    total_return = -result2[0]['amount_paid'] 
                row += 1
                sheet.write(row, 0, j, format_content_text)
                sheet.write(row, 1, session.start_at.strftime('%Y-%m-%d'), format_content_text)
                sheet.write(row, 2, session.name, format_content_text)
                sheet.write(row, 3, total_payment, format_content_float)
                sheet.write(row, 4, total_return, format_content_float)
       
                col1 = 5
                for payment_method in config_id.payment_method_ids:
                    result1 = self.env['pos.payment'].read_group([('session_id', '=', session.id), ('payment_method_id', '=', payment_method.id)], ['amount'], ['session_id'])
                    if result1:
                        sheet.write(row, col1, result1[0]['amount'], format_content_float)
                        sum_total ={
                            'payment_method': payment_method.name,
                            'amount':result1[0]['amount']
                           }
                        sum_total_list.append(sum_total)
                        col1 += 1
                    else:
                        sheet.write(row, col1, 0, format_content_float)
                        col1 += 1
                j += 1
                sum_total_payment += total_payment
                sum_return += total_return
                # sum_total_bank_payment += total_payment - total_cash_payment

            sheet.merge_range(row+1, 0, row+1, 2, 'Нийт', format_content_bold_text)
            sheet.write(row+1, 3, sum_total_payment, format_content_bold_float)
            sheet.write(row+1, 4, sum_return, format_content_bold_float)
            
            col2 =5
            for payment_method in config_id.payment_method_ids:
                total_amount = 0
                for sum_list in sum_total_list:
                    if sum_list['payment_method'] == payment_method.name:
                        total_amount += sum_list['amount']
                sheet.write(row+1, col2, total_amount, format_content_bold_float)
                col2 +=1
            row +=2           
        workbook.close()
        # set file data
        report_excel_output_obj.filedata = base64.b64encode(output.getvalue())
        # call export function
        return report_excel_output_obj.export_report()
       