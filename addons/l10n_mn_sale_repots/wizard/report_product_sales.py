# -*- coding: utf-8 -*-
import time
from datetime import date, datetime
import calendar
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

class ReportProductSales(models.TransientModel):

    _name = 'report.product.sales'
    _description = 'Generate XLSX report for Sale\'s'

    def get_group_by(self, context=None):
        res = [('manufacture',_('Manufacturer')),
               ('category',_('Category')),
               ('user',_('Salesperson')),
               ('partner',_('Partner')),
               ('team',_('Sales Team')),
               ('sale_type', _('Sale Type')),]
        #pos_obj = self.pool.get('pos.category')
        #if pos_obj:
        #    res += [('pos_categ',_('Pos Category'))]
        return res
    
    def _get_pos_install(self, context=None):
        '''
            Посын модуль суусан эсэхийг шалгана. 
        '''
        pos_obj = self.env['pos.order']
        if pos_obj:
            return True
        return False

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    warehouse_ids = fields.Many2many('stock.warehouse', 'report_product_sales_warehouse_rel','wizard_id', 'warehouse_id', 'Warehouse')
    
    date_from = fields.Date('From Date', required=True, default=lambda *a: time.strftime('%Y-01-01'))
    date_to = fields.Date('To Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    

    def _get_warehouse(self, context=None):
        user = self.env['res.users'].browse(uid)
        return user.property_warehouse_id
    
    def _get_team(self, context=None):
        user = self.env['res.users'].browse(uid)
        return ([user.default_section_id and user.default_section_id.id]) or []
    
    def _get_user(self, context=None):
        user = self.env['res.users'].browse(uid)
        return ([user and user.id]) or []

    # def export_report_xls(self):
       
    #     wiz = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'date_from': self.date_from,
    #         'date_to': self.date_to,
    #         'company_partner': self.company_id.partner_id.id,
    #         'warehouse_ids': self.warehouse_ids
    #          }
    #     return {
    #         'type': 'ir.actions.report',
    #         'wiz': {'model': 'report.product.sales',
    #                  'options': json.dumps(wiz, default=date_utils.json_default),
    #                  'output_format': 'xlsx',
    #                  'report_name': 'Борлуулалтын тайлан',
    #                  },
    #         'report_type': 'xlsx'
    #     }

    # Борлуулалтын мэдээлэл авах
    def get_sale_line(self, partner_id, warehouse_id, date_from, date_to):
        sale_wiz = []
        invoice_line_query = """
            SELECT rp.id as partner_id, rp.name as pname, rp.vat as vat, rp.phone as phone,  
            SUM(sol.qty_delivered)as qty, SUM(sol.price_unit * sol.qty_delivered * sol.discount/100)  AS discount,  
            SUM(sol.price_unit * sol.qty_delivered) AS so_price_total, 
            SUM(sol.price_total) as price_total, 
            SUM(aml.quantity)as invoice_qty, am.move_type as move_type, 
            SUM(aml.price_unit * aml.quantity * aml.discount/100)  AS invoice_discount, 
            SUM(aml.price_unit * aml.quantity) AS invoice_total 
                FROM sale_order_line AS sol 
                JOIN sale_order AS so ON so.id = sol.order_id
                JOIN res_partner AS rp ON rp.id = so.partner_id  
                JOIN sale_order_line_invoice_rel as solir ON solir.order_line_id = sol.id
                JOIN account_move_line AS aml On aml.id =  solir.invoice_line_id
                JOIN account_move AS am ON am.id = aml.move_id
                WHERE so.date_order >= %s AND so.date_order <= %s AND so.state in ('sale', 'done') AND so.source_id IS NULL AND so.partner_id=%s AND so.warehouse_id=%s 
                GROUP BY rp.id, rp.name, rp.vat, rp.phone, am.move_type;
              """
        params = date_from, date_to, partner_id, warehouse_id

        self._cr.execute(invoice_line_query, params)
        inv_line_query_obj = self._cr.dictfetchall()
        
        return inv_line_query_obj
     

    # Харилцагчийн мэдээлэл авах

    def get_lines(self, wiz, warehouse_id):
        lines = []
        date_from =  wiz['date_from'].strftime("%Y-%m-%d")# + ' 00:00:00'
        date_to =  wiz['date_to'].strftime("%Y-%m-%d") #+ ' 23:59:59'
        
        amount = return_amount = 0
        return_discount = return_qty = 0
        company_id = wiz['company_id'][0]
        vals = {}

        invoice_query = """
            SELECT rp.id AS partner_id, rp.name AS partner_name, rp.phone AS phone, rp.is_contract as is_contract, 
                rp.vat AS vat, rp.state_id AS district 
                FROM sale_order AS so
                JOIN res_partner AS rp ON rp.id = so.partner_id
                WHERE so.date_order >= %s AND so.date_order <= %s GROUP BY rp.id ORDER BY rp.name;
              """
        params = date_from, date_to
        print('params', params)
        self._cr.execute(invoice_query, params)
        inv_query_obj = self._cr.dictfetchall()
        print('inv_query_obj', inv_query_obj)
        for line in inv_query_obj:
            
            print('line', line)
            vals = {
                'partner_id': line['partner_id'],
                'partner_name': line['partner_name'],
                'phone':        line['phone'],
                'vat': line['vat'],
                'district': line['district'],
                'is_contract': line['is_contract'],
            }
            
            lines.append(vals)

        return lines

    def export_report_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.read()[0]
        
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

        for warehouse_id in wiz['warehouse_ids']:
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            sheet = workbook.add_worksheet(warehouse.name)
            sheet.set_landscape()

            report_name = u'Борлуулалтын дэлгэрэнгүй тайлан'
            filename = report_name

            sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
            sheet.merge_range(1, 1, 1, 14, u'Борлуулалтын дэлгэрэнгүй тайлан', format11)
            sheet.merge_range(2, 1, 2, 10, u'Эхлэх огноо: %s' %wiz['date_from'], format0)
            sheet.merge_range(3, 1, 3, 10, u'Дуусах огноо: %s' %wiz['date_to'], format0)
            sheet.merge_range(2, 11, 2, 13, u'Хэвлэсэн: %s' %datetime.datetime.now().strftime("%Y-%m-%d"), format0)
            sheet.merge_range(3, 11, 3, 13, u'Салбар: %s' %warehouse.name, format0)
            
            start_month = datetime. datetime. strptime(wiz['date_from'].strftime("%Y-%m-%d"), "%Y-%m-%d").month
           
            end_month = datetime. datetime. strptime(wiz['date_to'].strftime("%Y-%m-%d"), "%Y-%m-%d").month
            user = self.env['res.users'].browse(self.env.uid)
            tz = pytz.timezone(user.tz if user.tz else 'UTC')
            times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
            # sheet.merge_range('A8:G8', u'Тайлан хэвлэсэн: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
            row = 7
            sheet.set_column(0, 0, 2)
            sheet.set_column(1, 1, 50)
            sheet.set_column(3, 3, 18)
            sheet.set_column(4, 4, 18)
            # sheet.set_column(6, 6, 20)
            sheet.set_row(row+1, 50)
            sheet.merge_range(row, 0, row+1, 0, u'№', format1)
            sheet.merge_range(row, 1, row, 6, u'Харилцагчийн мэдээлэл', format1)
            sheet.write(row+1, 1, u'Харилцагч', format1)
            sheet.write(row+1, 2, u'Харилцагчийн регистр', format1)
            sheet.write(row+1, 3, u'Харилцагчийн Утас', format1)
            sheet.write(row+1, 4, u'Харилцагчийн Дүүрэг', format1)
            sheet.write(row+1, 5, u'Гэрээтэй эсэх', format1)
            sheet.write(row+1, 6, u'Авлагын үлдэгдэл', format1)
            if start_month == end_month:
                col = 7
                sheet.merge_range(row,col, row, col+6, str(start_month)+ u' сар', format1)
                sheet.write(row+1, col, u'Борлуулсан Тоо', format1)
                sheet.write(row+1, col+1, u'Буцаалтын Тоо', format1)
                sheet.write(row+1, col+2, u'Үнийн дүн', format1)
                sheet.write(row+1, col+3, u'Буцаалт', format1)
                sheet.write(row+1, col+4, u'Хөнгөлөлт', format1)
                sheet.write(row+1, col+5, u'Буцаалтын Хөнгөлөлт', format1)
                sheet.write(row+1, col+6, u'Цэвэр дүн', format1)
             
            elif start_month < end_month:
                sheet.merge_range(row,7, row, 13, u' Нийт', format1)
                sheet.write(row+1, 7, u'Борлуулсан Тоо', format1)
                sheet.write(row+1, 8, u'Буцаалтын Тоо', format1)
                sheet.write(row+1, 9, u'Үнийн дүн', format1)
                sheet.write(row+1, 10, u'Буцаалт', format1)
                sheet.write(row+1, 11, u'Хөнгөлөлт', format1)
                sheet.write(row+1, 12, u'Буцаалтын Хөнгөлөлт', format1)
                sheet.write(row+1, 13, u'Цэвэр дүн', format1)
                col = 14
                for i in range(start_month, end_month+1):
                    
                    # col += 1
                    sheet.merge_range(row,col, row, col+6, str(i) + u' сар', format1)
                    sheet.write(row+1, col, u'Борлуулсан Тоо', format1)
                    sheet.write(row+1, col+1, u'Буцаалтын Тоо', format1)
                    sheet.write(row+1, col+2, u'Үнийн дүн', format1)
                    sheet.write(row+1, col+3, u'Буцаалт', format1)
                    sheet.write(row+1, col+4, u'Хөнгөлөлт', format1)
                    sheet.write(row+1, col+5, u'Буцаалтын Хөнгөлөлт', format1)
                    sheet.write(row+1, col+6, u'Цэвэр дүн', format1)
                    col += 7
                   
            row +=2

            sheet.merge_range(row,0, row, 5, u'Нийт дүн', format1)
            sum_row = 9
            a = 10
            
            get_line = self.get_lines(wiz, warehouse.id)
            
            if start_month == end_month:    
                row +=1
                j = 0
                for each in get_line:
                    a += 1
                    amount_due = 0
                    district = u'Тодорхойгүй'
                    is_contract = u''
                    rcs = self.env['res.country.state'].search([('id', '=', each['district'],)])
                    if rcs:
                        district = rcs.name
                    partner_id = each['partner_id']

                    invoices = self.env['account.move'].search([('partner_id', '=', partner_id),
                        ('move_type','=','out_invoice'),
                        ('payment_state','!=', 'paid'),
                        ('state','=', 'posted')])
                    
                    for invoice in invoices:
                        amount_due += invoice.amount_residual

                    return_discount = return_amount = price_total = 0
                    if each['is_contract'] == 'contract':
                        is_contract = u'Гэрээтэй'
                    elif each['is_contract'] == 'loan_contract':
                        is_contract = u'Зээлийн Гэрээтэй'
                    elif each['is_contract'] == 'no_contract':
                        is_contract = u'Гэрээгүй'
                    sale_line =  self.get_sale_line(partner_id, warehouse.id, wiz['date_from'], wiz['date_to'])
                    if sale_line:
                        j += 1
                        for res_line in sale_line:
                            if res_line['partner_id'] == partner_id and res_line['move_type']=='out_invoice':
                                sheet.write(row, 0, j, font_size_8)
                                sheet.write(row, 1,res_line['pname'], font_size_8_l_b)
                                sheet.write(row, 2, res_line['vat'], font_size_8_l_b)
                                sheet.write(row, 3, res_line['phone'], font_size_8)
                                sheet.write(row, 4, district, font_size_8)
                                sheet.write(row, 5, is_contract, font_size_8)
                                sheet.write(row, 6, '', font_size_8)
                                sheet.write(row, 7, float(res_line['qty']), font_size_8)
                                sheet.write(row, 9, res_line['so_price_total'], font_size_8)
                                sheet.write(row, 11, res_line['discount'], font_size_8)
                                so_price_total =  res_line['so_price_total'] - res_line['discount']
                            elif res_line['partner_id'] == partner_id and res_line['move_type']=='out_refund':
                                sheet.write(row, 8, res_line['invoice_qty'], font_size_8)
                                return_amount = res_line['invoice_total']
                                sheet.write(row, 10, res_line['invoice_total'], font_size_8)
                                sheet.write(row, 13, res_line['invoice_discount'], font_size_8)
                                return_discount = res_line['invoice_discount']
                            sheet.write(row, 13, so_price_total, font_size_8)

                # #     sheet.write_formula(row, 35, 'SUM(F%s+I%s+L%s+O%s-U%s-X%s-AA%s-AD%s)'%(row+1,row+1,row+1,row+1,row+1,row+1,row+1,row+1), font_size_8)
                        row +=1
            else:
                row +=1
                j = 0
                for each in get_line:
                    amount_due = 0

                    district = u'Тодорхойгүй'
                    is_contract = ''
                    rcs = self.env['res.country.state'].search([('id', '=', each['district'],)])
                    if rcs:
                        district = rcs.name
                    j += 1
                    a += 1
                    partner_id = each['partner_id']
                    invoices = self.env['account.move'].search([('partner_id', '=', partner_id),
                        ('move_type','=','out_invoice'),
                        ('payment_state','!=', 'paid'),
                        ('state','=', 'posted')])
                    for invoice in invoices:
                        amount_due += invoice.amount_residual
                    if each['is_contract'] == 'contract':
                        is_contract = u'Гэрээтэй'
                    elif each['is_contract'] == 'no_contract':
                        is_contract = u'Гэрээгүй'
                    sheet.write(row, 0, j, font_size_8)
                    sheet.write(row, 1,each['partner_name'], font_size_8_l_b)
                    sheet.write(row, 2, each['vat'], font_size_8_l_b)
                    sheet.write(row, 3, each['phone'], font_size_8)
                    sheet.write(row, 4, district, font_size_8)
                    sheet.write(row, 5, is_contract, font_size_8)
                    sheet.write(row, 6, amount_due, font_size_8)
                    ############### Нийт дүнг харуулах #################
                    sale_line =  self.get_sale_line(partner_id, warehouse.id, wiz['date_from'], wiz['date_to'])
                    for res_line in sale_line:
                        if res_line['partner_id'] == partner_id and res_line['move_type']=='out_invoice':
                            sheet.write(row, 7, float(res_line['qty'] or 0), font_size_8)
                            sheet.write(row, 9, res_line['so_price_total'] or 0, font_size_8)
                            sheet.write(row, 11, res_line['discount'] or 0, font_size_8)
                            so_price_total =  res_line['so_price_total'] - res_line['discount']
                        elif res_line['partner_id'] == partner_id and res_line['move_type']=='out_refund':
                            sheet.write(row, 8, res_line['invoice_qty'] or 0, font_size_8)
                            return_amount = res_line['invoice_total'] - res_line['invoice_discount']
                            sheet.write(row, 10, res_line['invoice_total'] - res_line['invoice_discount'] or 0, font_size_8)
                            sheet.write(row, 12, res_line['invoice_discount'] or 0, font_size_8)
                            return_discount = res_line['invoice_discount']
                        sheet.write(row, 13, so_price_total or 0, font_size_8)
                    col = 13
                    for sar in range(start_month, end_month+1):
                        
                        currentDate =wiz['date_to']
                        
                        return_discount = return_amount = so_price_total = 0
                        firstDayOfMonth = datetime.date(currentDate.year, sar, 1)
                        lastDayOfMonth = datetime.date(currentDate.year, sar, calendar.monthrange(currentDate.year, sar)[1])
                        print(' wiz[date_from].month',  wiz['date_from'], lastDayOfMonth)
                        if sar == wiz['date_from'].month:
                            sale_line =  self.get_sale_line(partner_id, warehouse.id, wiz['date_from'], lastDayOfMonth)
                            for res_line in sale_line:
                                if res_line['partner_id'] == partner_id and res_line['move_type']=='out_invoice':
                                    sheet.write(row, col+1, float(res_line['qty'] or 0), font_size_8)
                                    sheet.write(row, col+3, res_line['so_price_total'] or 0, font_size_8)
                                    sheet.write(row, col+5, res_line['discount'] or 0, font_size_8)
                                    so_price_total =  res_line['so_price_total'] - res_line['discount']
                                elif res_line['partner_id'] == partner_id and res_line['move_type']=='out_refund':
                                    sheet.write(row, col +2, res_line['invoice_qty'] or 0, font_size_8)
                                    return_amount = res_line['invoice_total'] - res_line['invoice_discount']
                                    sheet.write(row, col+4, res_line['invoice_total'] - res_line['invoice_discount'] or 0, font_size_8)
                                    sheet.write(row, col+6, res_line['invoice_discount'] or 0, font_size_8)
                                    return_discount = res_line['invoice_discount']
                                sheet.write(row, col+7, so_price_total or 0, font_size_8)
                            col = col+7
                        elif sar != wiz['date_from'].month and wiz['date_to']> lastDayOfMonth:
                            sale_line =  self.get_sale_line(partner_id, warehouse.id, firstDayOfMonth, lastDayOfMonth)
                            len_sale_line = 0
                            for res_line in sale_line:
                                len_sale_line +=1
                                if res_line['partner_id'] == partner_id and res_line['move_type']=='out_invoice':
                                    sheet.write(row, col +1, float(res_line['qty'] or 0), font_size_8)
                                    sheet.write(row, col+3, res_line['so_price_total'] or 0, font_size_8)
                                    sheet.write(row, col+5, res_line['discount'] or 0, font_size_8)
                                    so_price_total =  res_line['so_price_total'] - res_line['discount']
                                elif res_line['partner_id'] == partner_id and res_line['move_type']=='out_refund':
                                    sheet.write(row, col +2, res_line['invoice_qty'] or 0, font_size_8)
                                    return_amount = res_line['invoice_total'] - res_line['invoice_discount']
                                    sheet.write(row, col+4, res_line['invoice_total'] - res_line['invoice_discount'] or 0, font_size_8)
                                    sheet.write(row, col+6, res_line['invoice_discount'] or 0, font_size_8)
                                    return_discount = res_line['invoice_discount']
                                sheet.write(row, col+7, so_price_total or 0, font_size_8)
                                # if len_sale_line == 1:
                            col = col+7
                       
                        elif sar != wiz['date_from'].month and  wiz['date_to']<= lastDayOfMonth:
                            sale_line =  self.get_sale_line(partner_id, warehouse.id, firstDayOfMonth, wiz['date_to'])
                            
                            for res_line in sale_line:
                                if res_line['partner_id'] == partner_id and res_line['move_type']=='out_invoice':
                                    sheet.write(row, col +1, float(res_line['qty'] or 0), font_size_8)
                                    sheet.write(row, col+3, res_line['so_price_total'] or 0, font_size_8)
                                    sheet.write(row, col+5, res_line['discount'] or 0, font_size_8)
                                    so_price_total =  res_line['so_price_total'] - res_line['discount']
                                elif res_line['partner_id'] == partner_id and res_line['move_type']=='out_refund':
                                    sheet.write(row, col +2, res_line['invoice_qty'] or 0, font_size_8)
                                    return_amount = res_line['invoice_total'] - res_line['invoice_discount'] 
                                    sheet.write(row, col+4, res_line['invoice_total'] - res_line['invoice_discount'] or 0, font_size_8)
                                    sheet.write(row, col+6, res_line['invoice_discount'] or 0, font_size_8)
                                    return_discount = res_line['invoice_discount']
                                sheet.write(row, col+7, so_price_total or 0, font_size_8)
                    row +=1 
            for scol in range(6, col+7): 
                col_name = xlsxwriter.utility.xl_col_to_name(scol)  
                sheet.write_formula(sum_row, scol, 'SUM(%s11:%s%s)'%(col_name, col_name,a), format1)
            # sheet.write_formula(sum_row, 6, 'SUM(scol11:G%s)'%a, format1)
            # sheet.write_formula(sum_row, 7, 'SUM(H11:H%s)'%a, format1)
            # sheet.write_formula(sum_row, 8, 'SUM(I11:I%s)'%a, format1)
            # sheet.write_formula(sum_row, 9, 'SUM(J11:J%s)'%a, format1)
            # sheet.write_formula(sum_row, 10, 'SUM(K11:K%s)'%a, format1)
            # sheet.write_formula(sum_row, 11, 'SUM(L11:L%s)'%a, format1)
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
