

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

class ReportProductSales(models.TransientModel):

    _name = 'report.price.comparison'
    _description = 'Generate XLSX report for Price Comparison'

    

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    date = fields.Date('Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    pricelist_ids = fields.Many2many('product.pricelist', 'price_comparison_report_rel','wizard_id', 'pricelist_id', 'Pricelist')
    product_ids = fields.Many2many('product.product', 'price_comparison_report_product_rel', 'wizard_id', 'product_id', 'Product')

    def export_report_xls(self):
       
        data = {
            'ids': self.ids,
            'model': self._name,
            'date': self.date,
            'pricelist_ids': self.pricelist_ids,
            'product_ids': self.product_ids
             }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'report.price.comparison',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Үнийн харьцуулалтын тайлан',
                     },
            'report_type': 'xlsx'
        }


    # Харилцагчийн мэдээлэл авах
    def get_products(self):
        products = []
        temp_ids = self.env['product.template'].search([('active','=', True), ('available_in_pos','=', True)])
        for temp in temp_ids:
           
            products.append(self.env['product.product'].search([('product_tmpl_id', '=', temp.id)]))
        return products

    def get_lines(self, data, warehouse_id):
        lines = []
        
        return lines

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
        sheet.merge_range(0, 1, 0, 8, u'Байгууллагын нэр: %s' %comp, format0)
        sheet.merge_range(1, 1, 1, 8, u'Үнийн харьцуулалтын тайлан', format11)
        
        
        sheet.merge_range(2, 11, 2, 7, u'Хэвлэсэн: %s' %datetime.datetime.now().strftime("%Y-%m-%d"), format0)
        
        row = 4
        sheet.set_column(0, 0, 2)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 30)
        sheet.set_row(5, 30)
        sheet.merge_range(row, 0, row+1, 0, u'№', format1)
        sheet.merge_range(row, 1, row, 4, u'Барааны мэдээлэл', format1)
        sheet.write(row+1, 1, u'Дотоод код', format1)
        sheet.write(row+1, 2, u'Баркод', format1)
        sheet.write(row+1, 3, u'Барааны нэр', format1)
        sheet.write(row+1, 4, u'Өртөг', format1)
        col = 5
        j = 1
        for price_list in wiz.pricelist_ids:
            col_count = len(wiz.pricelist_ids)
            
            sheet.merge_range(row, 5, row, col_count+4, u'Үнийн хүснэгт', format1)
            sheet.write(row+1, col, price_list.name, format1)
            sheet.set_column(col, col, 13)
            col +=1
        if wiz.product_ids:
            products = wiz.product_ids
        else:
            products = self.get_products() 
        row += 1
        for product in products:
            row += 1
            sheet.write(row, 0, j, font_size_8)
            sheet.write(row, 1, product.product_tmpl_id.default_code, font_size_8_l_b)
            sheet.write(row, 2, product.barcode, font_size_8_l_b)
            sheet.write(row, 3, product.name, font_size_8_l_b)
            sheet.write(row, 4, product.standard_price, font_size_8_l_b)
            col = 5
            for price_list in wiz.pricelist_ids:
                sale_price = price_list.get_product_price(product, 1, 1)
                sheet.write(row, col, sale_price, font_size_8)
                col += 1
            j += 1
                
            

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()    
