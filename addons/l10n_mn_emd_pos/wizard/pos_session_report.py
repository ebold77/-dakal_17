

# -*- coding: utf-8 -*-
import time
from datetime import date, datetime
import calendar
import pytz
import json
import datetime
import io
from odoo import api, fields, models, _
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import logging
logger = logging.getLogger(__name__)

class ReportPosSession(models.TransientModel):

    _name = 'report.pos.session'
    _description = 'Generate XLSX report for Pos session'

    

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    start_date = fields.Date('Start Date', required=True, default=lambda *a: time.strftime('2022-12-01'))
    end_date = fields.Date('End Date', required=True, default=lambda *a: time.strftime('2022-12-31'))
    config_ids = fields.Many2many('pos.config', 'pos_session_report_rel','wizard_id', 'config_id', 'Pos Config')
   

    def export_report_xls(self):
       
        data = {
            'ids': self.ids,
            'model': self._name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'config_ids': self.config_ids,
             }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'report.pos.session',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Посын Орлогын тайлан',
                     },
            'report_type': 'xlsx'
        }


    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.browse(data['ids'])
        
        comp = self.env.user.company_id.name
        
        format0 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format1 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'border': 1, 'bold': True, 'text_wrap': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center', 'border': 1})
        font_size_8_l_b = workbook.add_format({'font_size': 8, 'align': 'left', 'border': 1})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right', 'border': 1})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red', 'border': 1})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')


        
            
        sheet = workbook.add_worksheet('sheet')
        sheet.set_landscape()
        sheet.merge_range(0, 1, 0, 6, u'Байгууллагын нэр: %s' %comp, format0)
        sheet.merge_range(1, 1, 1, 6, u'Посын Орлогын тайлан', format11)
        
        
        sheet.merge_range(2, 5, 2,6, u'Хэвлэсэн: %s' %datetime.datetime.now().strftime("%Y-%m-%d"), format0)
        
        row = 4
        sheet.set_column(0, 0, 2)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        # sheet.set_row(5, 30)
        sheet.write(row, 0, u'№', format1)
        sheet.write(row, 1, u'Огноо', format1)
        sheet.write(row, 2, u'Сэшн', format1)
        sheet.write(row, 3, u'Нийт борлуулалт', format1)
        sheet.write(row, 4, u'Буцаалт', format1)
        sheet.write(row, 5, u'Банкны пос', format1)
        sheet.write(row, 6, u'Бэлэн', format1)
        col = 5
        for config_id in wiz.config_ids:
            sheet.merge_range(row+1, 0, row+1, 6, u'%s' %config_id.name, format1)
            row +=1
            session_ids = self.env['pos.session'].search([('config_id','=', config_id.id), 
                ('start_at','>=', wiz.start_date), ('start_at','<=', wiz.end_date)])
            sum_return = 0
            sum_total_payment = 0
            sum_total_cash_payment = 0
            sum_total_bank_payment = 0
            j = 1
            for session in session_ids.sorted(key=lambda x: x.start_at):
                total_return = 0
                total_payment = 0
                total_cash_payment = 0
                result = self.env['pos.payment'].read_group([('session_id', '=', session.id)], ['amount'], ['session_id'])
                if result:
                    total_payment = result[0]['amount']
                cash_payment_method = session.payment_method_ids.filtered('is_cash_count')[:1]
                result1 = self.env['pos.payment'].read_group([('session_id', '=', session.id), ('payment_method_id', '=', cash_payment_method.id)], ['amount'], ['session_id'])
                if result1:
                    total_cash_payment = result1[0]['amount']
                result2 = self.env['pos.order'].read_group([('session_id', '=', session.id),('amount_paid','<',0)], ['amount_paid'], ['session_id'])
                if result2:
                    total_return = -result2[0]['amount_paid'] 
                row += 1
                sheet.write(row, 0, j, font_size_8)
                sheet.write(row, 1, session.start_at.strftime('%Y-%m-%d'), font_size_8_l_b)
                sheet.write(row, 2, session.name, font_size_8_l_b)
                sheet.write(row, 3, total_payment, font_size_8_l_b)
                sheet.write(row, 4, total_return, font_size_8_l_b)
                sheet.write(row, 5, total_payment - total_cash_payment, font_size_8_l_b)
                sheet.write(row, 6, total_cash_payment, font_size_8_l_b)
                j += 1
                sum_total_payment += total_payment
                sum_total_cash_payment += total_cash_payment
                sum_return += total_return
                sum_total_bank_payment += total_payment - total_cash_payment

            sheet.merge_range(row+1, 0, row+1, 2, 'Нийт', format1)
            sheet.write(row+1, 3, sum_total_payment, format1)
            sheet.write(row+1, 4, sum_return, format1)
            sheet.write(row+1, 5, sum_total_bank_payment, format1)
            sheet.write(row+1, 6, sum_total_cash_payment, format1)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()    
