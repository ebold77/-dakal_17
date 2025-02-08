# -*- coding: utf-8 -*-
import time
from datetime import date, datetime
import pytz
import json
import datetime
import io
import base64
from odoo import api, fields, models, _
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import logging
logger = logging.getLogger(__name__)

class ProfitLossCalculationReport(models.TransientModel):

    _name = 'profit.calculation.report'
    _description = 'Generate XLSX report for profit loss'

    company_id = fields.Many2one('res.company', 'Company', readonly=True, index=True, default=lambda self: self.env.company.id)   
    start_date = fields.Date(string='Start Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    end_date = fields.Date(string='End Date', default=lambda *a: time.strftime('%Y-%m-%d'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    # def export_report_xls(self):
       
    #     data = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'start_date': self.start_date,
    #         'end_date': self.end_date,
    #         'company_partner': self.company_id.partner_id.id,
    #          }
    #     return {
    #         'type': 'ir.actions.report',
    #         'data': {'model': 'profit.calculation.report',
    #                  'options': json.dumps(data, default=date_utils.json_default),
    #                  'output_format': 'xlsx',
    #                  'report_name': 'Өртөгийн хувь тооцсон тайлан',
    #                  },
    #         'report_type': 'xlsx'
    #     }



    def get_lines(self, data):
        lines = []
        start_date =  data['start_date'] #+ ' 00:00:00'
        end_date =  data['end_date'] #+ ' 23:59:59'
        invoice_name = invoice_date = False
        invoice_amount = 0
        invoice_payed_amount = 0
        company_id = data['company_partner']
        vals = {}
        
        statement_query = """
               SELECT rp.id AS partner_id, rp.name AS partner_name, abs.name, absl.payment_ref, abs.date as statement_date, 
                    absl.id as line_id, absl.create_date, absl.amount, aj.name AS journal_name, absl.move_id as move_id FROM account_bank_statement_line AS absl
               JOIN res_partner AS rp ON rp.id = absl.partner_id
               JOIN account_bank_statement AS abs ON abs.id = absl.statement_id 
               JOIN account_journal AS aj ON aj.id = abs.journal_id 
               JOIN account_move AS am ON am.id = absl.move_id 
               WHERE abs.date >= %s
               AND abs.date <= %s
               AND rp.id != %s
               AND absl.amount>0 ORDER BY abs.date """
        params = start_date, end_date, str(company_id)
        
        self._cr.execute(statement_query, params)
        bsl_query_obj = self._cr.dictfetchall()
        for line in bsl_query_obj:
            bs_line =  self.env['account.bank.statement.line'].browse(line['line_id'])    
            if bs_line.date >= datetime.datetime.strptime(data['start_date'], '%Y-%m-%d').date() and \
                bs_line.date <= datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date():
                bs_line_date = (bs_line.date).strftime("%Y-%m-%d")
                
                am_id = self.env['account.move'].search([('id','=', line['move_id'])])
                # reconciled_lines = am_id.open_reconcile_view()
                count_line = 0
                for aml in self.env['account.move.line'].search([('move_id','=', am_id.id),('debit','=', 0)]):
                    if aml:
                        vals = {
                            'partner_name': line['partner_name'],
                            'name': line['name'],
                            'payment_ref': line['payment_ref'],
                            'date':  bs_line_date,
                            'payed_amount': line['amount'],
                            'journal_name': line['journal_name'],
                            'invoice_date': '',
                            'invoice_name': '',
                            'invoice_amount': '',
                            'invoice_payed_amount': aml.credit,
                            'invoice_partner': '',
                            'invoice_user':'',
                            'cost_amount': 0,
                            'sale_income_amount': 0,
                            'aml_id': aml.id
                        }
                        invoice_payed_amount = aml.credit
                        rec_lines = aml._reconciled_lines()
                        for rec_line_id in rec_lines:
                            if rec_line_id != aml.id:
                                rec_line = self.env['account.move.line'].browse(rec_line_id)
                                sale_income_amount = cost_amount = 0
                                if rec_line.date<= aml.date:
                                    for cost_line in rec_line.move_id.line_ids:
                                        if cost_line.account_id.user_type_id.id==17 and cost_line.debit>0:
                                            cost_amount += cost_line.debit
                                        if cost_line.account_id.user_type_id.id==13 and cost_line.credit>0:
                                            sale_income_amount += cost_line.credit
                                    if rec_line.debit > 0:
                                        
                                        count_line += 1
                                        if rec_line.move_id.invoice_date:
                                            invoice_date = (rec_line.move_id.invoice_date).strftime("%Y-%m-%d")
                                        else:
                                            invoice_date = ''
                                        invoice_name = rec_line.move_id.name
                                        invoice_amount = rec_line.move_id.amount_total
                                        present =  invoice_payed_amount * 100 /invoice_amount
                                        
                                        cost_amount = cost_amount * present /100
                                        sale_income_amount = sale_income_amount * present/100
                                        if count_line == 1:
                                            vals['invoice_date'] = invoice_date
                                            vals['invoice_name'] = invoice_name
                                            vals['invoice_amount'] = invoice_amount
                                            vals['invoice_partner'] = rec_line.move_id.partner_id.name
                                            vals['invoice_user'] = rec_line.move_id.invoice_user_id.name
                                            vals['cost_amount'] = cost_amount
                                            vals['sale_income_amount'] = sale_income_amount
                                        else:
                                            vals['invoice_date'] = invoice_date
                                            vals['invoice_name'] = invoice_name
                                            vals['invoice_amount'] = invoice_amount
                                            vals['invoice_partner'] = rec_line.move_id.partner_id.name
                                            vals['invoice_user'] = rec_line.move_id.invoice_user_id.name
                                            vals['cost_amount'] = cost_amount
                                            vals['sale_income_amount'] = sale_income_amount
                                            vals['payed_amount'] = ''
                                        
                                    lines.append(vals)
            else:
                continue

        return lines

    def export_report_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.read()[0]
        
        comp = self.env.user.company_id.name
        company_partner = self.company_id.partner_id.id
        wiz['company_partner'] = company_partner
        
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

        report_name = u'Өртөгийн хувь тооцсон тайлан'
        filename = report_name
        
            
        sheet = workbook.add_worksheet("sheet")
        sheet.set_landscape()
        sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
        sheet.merge_range(1, 1, 1, 14, u'Өртөгийн хувь тооцсон тайлан', format11)
        sheet.merge_range(2, 1, 2, 10, u'Эхлэх огноо: %s' %wiz['start_date'], format0)
        sheet.merge_range(3, 1, 3, 10, u'Дуусах огноо: %s' %wiz['end_date'], format0)
        sheet.merge_range(3, 11, 3, 13, u'Өртгийн хувь:', format0)
        sheet.write_formula(3, 14, '=O9/M9')
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else 'UTC')
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        # sheet.merge_range('A8:G8', u'Тайлан хэвлэсэн: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
        row = 5
        sheet.set_column(0, 0, 2)
        sheet.set_column(1, 1, 20)
        sheet.set_row(row+2, 50)
        sheet.merge_range(row, 0, row+2, 0, u'№', format1)
        sheet.merge_range(row, 1, row+2, 1, u'Харилцагч', format1)
        sheet.merge_range(row,2, row, 6, u'Төлбөр', format1)
        sheet.merge_range(row+1, 2, row+2, 2, u'Журнал', format1)
        sheet.merge_range(row+1, 3, row+2, 3, u'Эх Баримт', format1)
        sheet.merge_range(row+1, 4, row+2, 4, u'Гүйлгээний утга', format1)
        sheet.merge_range(row+1, 5, row+2, 5, u'Төлсөн огноо', format1)
        sheet.merge_range(row+1, 6, row+2, 6, u'Төлсөн дүн', format1)
        sheet.merge_range(row,7, row, 14, u'Нэхэмжлэл', format1)
        sheet.merge_range(row+1, 7, row+2, 7, u'Нэхэмжилсэн дугаар', format1)
        sheet.merge_range(row+1, 8, row+2, 8, u'Харилцагч', format1)
        sheet.merge_range(row+1, 9, row+2, 9, u'Борлуулалгч', format1)
        sheet.merge_range(row+1, 10, row+2, 10, u'Нэхэмжлэлийн огноо', format1)
        sheet.merge_range(row+1, 11, row+2, 11, u'Нэхэмжлэлийн дүн', format1)
        sheet.merge_range(row+1, 12, row+2, 12, u'БО дүн', format1)
        sheet.merge_range(row+1, 13, row+2, 13, u'Нэхэмжлэлээс төлсөн дүн', format1)
        sheet.merge_range(row+1, 14, row+2, 14, u'Өртөгийн дүн', format1)

        

        row +=3

        sheet.merge_range(row,0, row, 4, u'Нийт дүн', format1)
        sum_row = a = 8

        
        row +=1
        j = 0
        get_line = self.get_lines(wiz)
        
        for each in get_line:
            
            j += 1
            sheet.write(row, 0, j, font_size_8)
            sheet.write(row, 1, each['partner_name'], font_size_8_l_b)
            sheet.write(row, 2, each['journal_name'], font_size_8_l_b)
            sheet.write(row, 3,each['name'], font_size_8_l_b)
            sheet.write(row, 4, each['payment_ref'], font_size_8_l_b)
            sheet.write(row, 5, each['date'], font_size_8)
            sheet.write(row, 6, each['payed_amount'], font_size_8)
            sheet.write(row, 7, each['invoice_name'], font_size_8)
            sheet.write(row, 8, each['invoice_partner'], font_size_8)
            sheet.write(row, 9, each['invoice_user'], font_size_8)
            sheet.write(row, 10, each['invoice_date'], font_size_8)
            sheet.write(row, 11, each['invoice_amount'], font_size_8)
            sheet.write(row, 12, each['sale_income_amount'], font_size_8)
            sheet.write(row, 13, each['invoice_payed_amount'], font_size_8)
            sheet.write(row, 14, each['cost_amount'], font_size_8)
            sheet.write(row, 15, each['aml_id'], font_size_8)
        

        #     sheet.write_formula(row, 35, 'SUM(F%s+I%s+L%s+O%s-U%s-X%s-AA%s-AD%s)'%(row+1,row+1,row+1,row+1,row+1,row+1,row+1,row+1), font_size_8)
            row +=1
        a = row
        sheet.write_formula(sum_row, 6, 'SUM(G10:G%s)'%a, format1)
        sheet.write_formula(sum_row, 11, 'SUM(L10:L%s)'%a, format1)
        sheet.write_formula(sum_row, 12, 'SUM(M10:M%s)'%a, format1)
        sheet.write_formula(sum_row, 13, 'SUM(N10:N%s)'%a, format1)
        sheet.write_formula(sum_row, 14, 'SUM(O10:O%s)'%a, format1)

        sheet.merge_range(row+1, 2, row+1, 8, u'Гүйцэтгэсэн:\t\t\t\t\t\t/%s/'%user.name, font_size_8_l)
        sheet.merge_range(row+3, 2, row+3, 8, u'Ерөнхий нягтлан бодогч: \t\t\t\t\t\t/\t\t\t\t\t\t/' , font_size_8_l)

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        output.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=datas&download=true&filename='+filename,
        }   
