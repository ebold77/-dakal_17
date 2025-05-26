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

class StockProductBalance(models.TransientModel):
    _name = 'stock.product.balance'
    _description = 'Generate XLSX report for stock product balance between 2 dates'

    def get_group_by(self):
        res = [('manufacture', _('Manufacturer')),
               ('category', _('Category'))]
        pos_obj = self.pool.get('pos.category')
        if pos_obj:
            res += [('pos_categ', _('Pos Category'))]
        return res

    def _get_pos_install(self):
        '''
            Посын модуль суусан эсэхийг шалгана.
        '''
        pos_obj = self.pool.get('pos.order')
        if pos_obj:
            return True
        return False

    company_id = fields.Many2one('res.company', 'Company', readonly=True, index=True, default=lambda self: self.env.company.id)
    # warehouse_ids = fields.Many2many('stock.warehouse', 'stock_inventory_statement_warehouse_rel', 'wizard_id', 'warehouse_id', 'Warehouse')
    prod_categ_ids = fields.Many2many('product.category', 'stock_product_balance_prod_categ_rel', 'wizard_id', 'prod_categ_id', 'Product Category')  # domain=['|',('parent_id','=',False),('parent_id.parent_id','=',False)]),
    product_ids = fields.Many2many('product.product', 'stock_product_balance_product_rel', 'wizard_id', 'product_id', 'Product')
    # partner_ids = fields.Many2many('res.partner', 'stock_inventory_statement_partner_rel', 'wizard_id', 'partner_id', 'Partner')
   
    start_date = fields.Date(string='Start Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    end_date = fields.Date(string='End Date', default=lambda *a: time.strftime('%Y-%m-%d'))
    
    pos_install = fields.Boolean('Pos Install')
  
    # show_package = fields.Boolean('Show package?')
    pricelist_id =  fields.Many2one('product.pricelist', string="Pricelist", required=True,)

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    
    # def export_report_xls(self):
       
    #     data = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'start_date': self.start_date,
    #         'end_date': self.end_date,
    #          }
    #     return {
    #         'type': 'ir.actions.report',
    #         'data': {'model': 'stock.product.balance',
    #                  'options': json.dumps(data, default=date_utils.json_default),
    #                  'output_format': 'xlsx',
    #                  'report_name': 'Бараа материалын үлдэгдэл тайлан',
    #                  },
    #         'report_type': 'xlsx'
    #     }


    def get_lines(self, wiz, prod_categ_ids, product_ids, pricelist_id):
        lines = []
        start_date =  wiz['start_date'] 
        end_date =  wiz['end_date'] 

        if prod_categ_ids:
            categ_products = self.env['product.product'].search([('categ_id', 'in', prod_categ_ids)])

        else:
            categ_products = self.env['product.product'].search([])
        product_ids = tuple([pro_id.id for pro_id in categ_products])
        pricelist = self.env['product.pricelist'].search([('id', '=', pricelist_id[0])])
        for obj in categ_products:

            # sale_price = pricelist_id.get_product_price(obj , 1, 1)
            sale_price = pricelist._get_product_price(
                    product=obj,
                    quantity=1.0,
                    # currency=self.company_id.currency_id,
                    date= end_date,
        )
            
            virtual_available = obj.with_context().virtual_available
            outgoing_qty = obj.with_context().outgoing_qty
            incoming_qty = obj.with_context().incoming_qty
            available_qty = virtual_available + outgoing_qty - incoming_qty
            value = available_qty * obj.standard_price
            if virtual_available != 0 or incoming_qty != 0 or \
                outgoing_qty != 0 or available_qty != 0:
               
                vals = {
                    'default_code': obj.default_code,
                    'name': obj.name,
                    'uom': obj.uom_id.name,
                    'category': obj.categ_id.name,
                    'cost_price': obj.standard_price,
                    # 'available': available_qty,
                    # 'virtual': virtual_available,
                    # 'incoming': incoming_qty,
                    # 'outgoing': outgoing_qty,
                    'initial_balance': obj.with_context({'to_date': start_date}).qty_available,
                    'net_on_hand': obj.with_context({'to_date': end_date}).qty_available,
                    # 'total_value': value,
                    # 'sale_value': sale_value,
                    # 'pos_sale_value': pos_sale_value,
                    # 'purchase_value': purchase_value,
                    'sale_price': sale_price,
                    # 'inv_in_value': inv_in_value,
                    # 'inv_out_value': inv_out_value,
                    # 'trans_in_value': trans_in_value,
                    # 'trans_out_value': trans_out_value,
                    # 'sale_return_value': sale_return_value,
                    # 'pos_return_value': pos_return_value,
                    # 'purchace_return_value': purchace_return_value,
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
         
        filename = 'Stock Balance Report'
            
        sheet = workbook.add_worksheet("Balance")
        sheet.set_landscape()
        sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
        sheet.merge_range(1, 1, 1, 10, u'Бараа материалын үлдэгдэл', format0)
        sheet.merge_range(2, 1, 2, 10, u'Эхлэх огноо: %s' %wiz['start_date'], format0)
        sheet.merge_range(3, 1, 3, 10, u'Дуусах огноо: %s' %wiz['end_date'], format0)
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else 'UTC')
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        # sheet.merge_range('A8:G8', u'Тайлан хэвлэсэн: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
        row = 5
        sheet.set_column(0, 0, 2)
        sheet.set_column(2, 2, 20)
        sheet.set_row(row+2, 50)
        sheet.merge_range(row, 0, row+2, 0, u'№', format1)
        sheet.merge_range(row, 1, row+2, 1, u'Дотоод код', format1)
        sheet.merge_range(row, 2, row+2, 2, u'Бараа материал', format1)
        sheet.merge_range(row, 3, row+2, 3, u'Хэмжих нэгж', format1)
        sheet.merge_range(row, 4, row+2, 4, u'Борлуулах үнэ', format1)

        sheet.merge_range(row, 5, row, 7, u'Эхний үлдэгдэл', format1)
        sheet.merge_range(row+1, 5, row+2, 5, u'Тоо хэмжээ', format1)
        sheet.merge_range(row+1, 6, row+2, 6, u'Борлуулах үнийн дүн', format1)
        sheet.merge_range(row+1, 7, row+2, 7, u'Өртөгийн дүн', format1)

        sheet.merge_range(row, 8, row, 10, u'Эцсийн үлдэгдэл', format1)
        sheet.merge_range(row+1, 8, row+2, 8, u'Тоо хэмжээ', format1)
        sheet.merge_range(row+1, 9, row+2, 9, u'Борлуулах үнийн дүн', format1)
        sheet.merge_range(row+1, 10, row+2, 10, u'Өртөгийн дүн', format1)

        

        row +=3

        sheet.merge_range(row,0, row, 4, u'Нийт дүн', format1)
        sum_row = a = 8

        
        row +=1
        j = 0
        get_line = self.get_lines(wiz, wiz['prod_categ_ids'], wiz['product_ids'], wiz['pricelist_id'])
        for each in get_line:
            j += 1
            sheet.write(row, 0, j, font_size_8)
            sheet.write(row, 1, each['default_code'], font_size_8)
            sheet.write(row, 2,each['name'], font_size_8_l_b)
            sheet.write(row, 3, each['uom'], font_size_8)
            sheet.write(row, 4, each['sale_price'], font_size_8)
            if each['initial_balance'] < 0:
                sheet.write(row, 5, each['initial_balance'], red_mark)
                sheet.write(row, 6, each['initial_balance'] * each['sale_price'], font_size_8)
                sheet.write(row, 7, each['initial_balance'] * each['cost_price'], font_size_8)
            else:
                sheet.write(row, 5, each['initial_balance'], font_size_8)
                sheet.write(row, 6, each['initial_balance'] * each['sale_price'], font_size_8)
                sheet.write(row, 7, each['initial_balance'] * each['cost_price'], font_size_8)



            if each['net_on_hand'] < 0:
                sheet.write(row, 8, each['net_on_hand'], red_mark)
                sheet.write(row, 9, each['net_on_hand'] * each['sale_price'], red_mark)
                sheet.write(row, 10, each['net_on_hand'] * each['cost_price'], font_size_8)
            else:
                sheet.write(row, 8, each['net_on_hand'], font_size_8)
                sheet.write(row, 9, each['net_on_hand'] * each['sale_price'], font_size_8)
                sheet.write(row, 10, each['net_on_hand'] * each['cost_price'], font_size_8)

            # sheet.write_formula(row, 35, 'SUM(F%s+I%s+L%s+O%s-U%s-X%s-AA%s-AD%s)'%(row+1,row+1,row+1,row+1,row+1,row+1,row+1,row+1), font_size_8)
            row +=1
        a = row
        sheet.write_formula(sum_row, 5, 'SUM(F10:F%s)'%a, format1)
        sheet.write_formula(sum_row, 6, 'SUM(G10:G%s)'%a, format1)
        sheet.write_formula(sum_row, 7, 'SUM(H10:H%s)'%a, format1)
        sheet.write_formula(sum_row, 8, 'SUM(I10:I%s)'%a, format1)
        sheet.write_formula(sum_row, 9, 'SUM(J10:J%s)'%a, format1)
        sheet.write_formula(sum_row, 10, 'SUM(K10:K%s)'%a, format1)
       

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

