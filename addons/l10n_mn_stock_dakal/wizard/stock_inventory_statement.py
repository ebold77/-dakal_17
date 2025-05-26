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

class StockInventoryStatement(models.TransientModel):
    _name = 'stock.inventory.statement'
    _description = 'Generate XLSX report for stock move between 2 dates'

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
    warehouse_ids = fields.Many2many('stock.warehouse', 'stock_inventory_statement_warehouse_rel', 'wizard_id', 'warehouse_id', 'Warehouse')
    prod_categ_ids = fields.Many2many('product.category', 'stock_inventory_statement_prod_categ_rel', 'wizard_id', 'prod_categ_id', 'Product Category')  # domain=['|',('parent_id','=',False),('parent_id.parent_id','=',False)]),
    product_ids = fields.Many2many('product.product', 'stock_inventory_statement_product_rel', 'wizard_id', 'product_id', 'Product')
    partner_ids = fields.Many2many('res.partner', 'stock_inventory_statement_partner_rel', 'wizard_id', 'partner_id', 'Partner')
   
    start_date = fields.Date(string='Start Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    end_date = fields.Date(string='End Date', default=lambda *a: time.strftime('%Y-%m-%d'))
    
    pos_install = fields.Boolean('Pos Install')
  
    show_package = fields.Boolean('Show package?')
    pricelist_id =  fields.Many2one('product.pricelist', string="Pricelist", required=True,)

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    
    # def export_report_xls(self):
       
    #     wiz = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'start_date': self.start_date,
    #         'end_date': self.end_date,
    #          }
    #     return {
    #         'type': 'ir.actions.report',
    #         'wiz': {'model': 'stock.inventory.statement',
    #                  'options': json.dumps(wiz, default=date_utils.json_default),
    #                  'output_format': 'xlsx',
    #                  'report_name': 'Агуулахын нөөцийн тайлан',
    #                  },
    #         'report_type': 'xlsx'
    #     }


    def get_lines(self, wiz, warehouse, partner_ids, prod_categ_ids, product_ids, pricelist_id, location_id):
        lines = []
        start_date =  wiz['start_date'] # + ' 00:00:00'
        end_date =  wiz['end_date'] #+ ' 23:59:59'
   
        if prod_categ_ids:
            categ_products = self.env['product.product'].search([('categ_id', 'in', prod_categ_ids.ids)])

        else:
            categ_products = self.env['product.product'].search([])
        product_ids = tuple([pro_id.id for pro_id in categ_products])
       
        sale_query = """
               SELECT sum(s_o_l.qty_delivered) AS product_uom_qty, s_o_l.product_id FROM sale_order_line AS s_o_l
               JOIN sale_order AS s_o ON s_o_l.order_id = s_o.id
               WHERE s_o.state IN ('sale','done')
               AND s_o.warehouse_id = %s
               AND s_o.date_order >= %s
               AND s_o.date_order <= %s
               AND s_o_l.product_id in %s group by s_o_l.product_id"""
        pos_query = """
               SELECT sum(pos_l.qty) AS product_uom_qty, pos_l.product_id FROM pos_order_line AS pos_l
               JOIN pos_order AS pos ON pos_l.order_id = pos.id
               JOIN pos_session AS pos_s ON pos.session_id = pos_s.id
               JOIN pos_config AS pos_conf ON pos_s.config_id = pos_conf.id
               JOIN stock_picking_type AS spt ON pos_conf.picking_type_id = spt.id
               WHERE pos.state IN ('paid','done')
               AND spt.warehouse_id = %s
               AND pos.date_order >= %s
               AND pos.date_order <= %s
               AND pos_l.qty > 0 
               AND pos_l.product_id in %s group by pos_l.product_id"""
        purchase_query = """
               SELECT sum(p_o_l.qty_received) AS product_qty, p_o_l.product_id FROM purchase_order_line AS p_o_l
               JOIN purchase_order AS p_o ON p_o_l.order_id = p_o.id
               INNER JOIN stock_picking_type AS s_p_t ON p_o.picking_type_id = s_p_t.id
               WHERE p_o.state IN ('purchase','done')
               AND s_p_t.warehouse_id = %s 
               AND p_o.date_order >= %s
               AND p_o.date_order <= %s
               AND p_o_l.product_id in %s group by p_o_l.product_id"""
        inventory_income_query = """
               SELECT sum(sm_l.quantity) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS sl ON sm_l.location_id = sl.id
               WHERE s_m.state = 'done' 
               AND sl.usage >= 'inventory'
               AND s_m.date >= %s
               AND s_m.date <= %s  
               AND s_m.location_dest_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        inventory_expense_query = """
               SELECT sum(sm_l.quantity) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS sl ON sm_l.location_dest_id = sl.id
               WHERE s_m.state = 'done' 
               AND sl.usage >= 'inventory'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        transit_income_query = """
               SELECT sum(sm_l.quantity) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='transit'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_dest_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        transit_out_query = """
               SELECT sum(sm_l.quantity) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_dest_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='transit'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        return_in_query = """
               SELECT sum(sm_l.quantity) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='customer'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_dest_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        return_out_query = """
               SELECT sum(sm_l.quantity) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_dest_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='supplier'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""


        params = warehouse, start_date, end_date, product_ids if product_ids else (0, 0)
        self._cr.execute(sale_query, params)
        sol_query_obj = self._cr.dictfetchall()

        self._cr.execute(pos_query, params)
        posl_query_obj = self._cr.dictfetchall()
        
        params = warehouse, start_date, end_date, product_ids if product_ids else (0, 0)
        self._cr.execute(purchase_query, params)
        pol_query_obj = self._cr.dictfetchall()


        params = start_date, end_date, location_id, product_ids if product_ids else (0, 0)
        print('inventory_income_query============', params)
        self._cr.execute(inventory_income_query, params)
        in_inv_query_obj = self._cr.dictfetchall()
        
        self._cr.execute(inventory_expense_query, params)
        out_inv_query_obj = self._cr.dictfetchall()
        
        wh_obj = self.env['stock.warehouse'].search([('id', '=', warehouse)])
        
        params = start_date, end_date, wh_obj.wh_input_stock_loc_id.id, product_ids if product_ids else (0, 0)
        self._cr.execute(transit_income_query, params)
        transit_in_query_obj = self._cr.dictfetchall()
        
        params = start_date, end_date, wh_obj.wh_output_stock_loc_id.id, product_ids if product_ids else (0, 0)
        self._cr.execute(transit_out_query, params)
        transit_out_query_obj = self._cr.dictfetchall()

        params = start_date, end_date, wh_obj.lot_stock_id.id, product_ids if product_ids else (0, 0)
       
        self._cr.execute(return_in_query, params)
        pos_return_in_query_obj = self._cr.dictfetchall()
        
        
        params = start_date, end_date, wh_obj.wh_output_stock_loc_id.id, product_ids if product_ids else (0, 0)
        self._cr.execute(return_in_query, params)
        sale_return_in_query_obj = self._cr.dictfetchall()

        params = start_date, end_date, wh_obj.wh_input_stock_loc_id.id, product_ids if product_ids else (0, 0)
        self._cr.execute(return_out_query, params)
        purchace_return_in_query_obj = self._cr.dictfetchall()
        
        for obj in categ_products:
            sale_return_value =sale_value = 0
            purchace_return_value = purchase_value = 0
            pos_return_value = pos_sale_value = 0
            inv_out_value = inv_in_value = 0
            trans_in_value = trans_out_value = 0
            # sale_price = pricelist_id.get_product_price(obj , 1, 1)
            pricelist = self.env['product.pricelist'].search([('id', '=', pricelist_id[0])])
            sale_price = pricelist._get_product_price(
                    product=obj,
                    quantity=1.0,
                    # currency=self.company_id.currency_id,
                    date= end_date)
        
            for sol_product in sol_query_obj:
                if sol_product['product_id'] == obj.id:
                    sale_value = sol_product['product_uom_qty']

            for posl_product in posl_query_obj:
                if posl_product['product_id'] == obj.id:
                    pos_sale_value = posl_product['product_uom_qty']


            for pol_product in pol_query_obj:
                if pol_product['product_id'] == obj.id:
                    purchase_value = pol_product['product_qty']
            for i_in_product in in_inv_query_obj:
                if i_in_product['product_id'] == obj.id:
                    inv_in_value = i_in_product['product_qty']

            for i_out_product in out_inv_query_obj:
                if i_out_product['product_id'] == obj.id:
                    inv_out_value = i_out_product['product_qty']

            for trans_in_product in transit_in_query_obj:
                if trans_in_product['product_id'] == obj.id:
                    trans_in_value = trans_in_product['product_qty']

            for trans_out_product in transit_out_query_obj:
                if trans_out_product['product_id'] == obj.id:
                    trans_out_value = trans_out_product['product_qty']

            for return_product in pos_return_in_query_obj:
                if return_product['product_id'] == obj.id:
                    pos_return_value = return_product['product_qty']

            for return_product in sale_return_in_query_obj:
                if return_product['product_id'] == obj.id:
                    sale_return_value = return_product['product_qty']

            for po_return_product in purchace_return_in_query_obj:
                if po_return_product['product_id'] == obj.id:
                    purchace_return_value = po_return_product['product_qty']

            virtual_available = obj.with_context({'warehouse': warehouse}).virtual_available
            outgoing_qty = obj.with_context({'warehouse': warehouse}).outgoing_qty
            incoming_qty = obj.with_context({'warehouse': warehouse}).incoming_qty
            available_qty = virtual_available + outgoing_qty - incoming_qty
            value = available_qty * obj.standard_price
            if virtual_available != 0 or incoming_qty != 0 or \
                outgoing_qty != 0 or available_qty != 0 or \
                trans_in_value != 0 or trans_out_value != 0 or \
                sale_return_value != 0 or pos_return_value != 0:
                vals = {
                    'default_code': obj.default_code,
                    'name': obj.name,
                    'uom': obj.uom_id.name,
                    'category': obj.categ_id.name,
                    'cost_price': obj.standard_price,
                    'available': available_qty,
                    'virtual': virtual_available,
                    'incoming': incoming_qty,
                    'outgoing': outgoing_qty,
                    'initial_balance': obj.with_context({'warehouse': warehouse, 'to_date': start_date}).qty_available,
                    'net_on_hand': obj.with_context({'warehouse': warehouse, 'to_date': end_date}).qty_available,
                    'total_value': value,
                    'sale_value': sale_value,
                    'pos_sale_value': pos_sale_value,
                    'purchase_value': purchase_value,
                    'sale_price': sale_price,
                    'inv_in_value': inv_in_value,
                    'inv_out_value': inv_out_value,
                    'trans_in_value': trans_in_value,
                    'trans_out_value': trans_out_value,
                    'sale_return_value': sale_return_value,
                    'pos_return_value': pos_return_value,
                    'purchace_return_value': purchace_return_value,
                }
                lines.append(vals)

        return lines

    def export_report_xls(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.read()[0]
        print('wiz=======================', wiz)
        
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

        filename = u'Агуулахын нөөцийн тайлан'
        
        for warehouse_id in wiz['warehouse_ids']:
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            sheet = workbook.add_worksheet(warehouse.name)
            sheet.set_landscape()
            sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
            sheet.merge_range(1, 1, 1, 10, u'Агуулахын нөөцийн тайлан', format0)
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

            sheet.merge_range(row,8, row, 19, u'Орлого', format1)

            sheet.merge_range(row+1, 8, row+1, 10, u'Худалдан авалт', format1)
            sheet.write(row+2, 8, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 9, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 10, u'Өртөгийн дүн', format1)

            sheet.merge_range(row+1, 11, row+1, 13, u'Нөхөн дүүргэлт', format1)
            sheet.write(row+2, 11, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 12, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 13, u'Өртөгийн дүн', format1)

            sheet.merge_range(row+1,14, row+1, 16, u'Тооллого', format1)
            sheet.write(row+2, 14, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 15, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 16, u'Өртөгийн дүн', format1)

            sheet.merge_range(row+1, 17, row+1, 19, u'Буцаалт', format1)
            sheet.write(row+2, 17, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 18, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 19, u'Өртөгийн дүн', format1)


            sheet.merge_range(row, 20, row, 31, u'Зарлага', format1)
            sheet.merge_range(row+1, 20, row+1, 22, u'Борлуулалт', format1)
            sheet.write(row+2, 20, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 21, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 22, u'Өртөгийн дүн', format1)

            sheet.merge_range(row+1, 23, row+1, 25, u'Нөхөн дүүргэлт', format1)
            sheet.write(row+2, 23, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 24, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 25, u'Өртөгийн дүн', format1)

            sheet.merge_range(row+1, 26, row+1, 28, u'Тооллого', format1)
            sheet.write(row+2, 26, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 27, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 28, u'Өртөгийн дүн', format1)


            sheet.merge_range(row+1, 29, row+1, 31, u'ХА Буцаалт', format1)
            sheet.write(row+2, 29, u'Тоо хэмжээ', format1)
            sheet.write(row+2, 30, u'Борлуулах үнийн дүн', format1)
            sheet.write(row+2, 31, u'Өртөгийн дүн', format1)
            

            sheet.merge_range(row, 32, row, 34, u'Эцсийн үлдэгдэл', format1)
            sheet.merge_range(row+1, 32, row+2, 32, u'Тоо хэмжээ', format1)
            sheet.merge_range(row+1, 33, row+2, 33, u'Борлуулах үнийн дүн', format1)
            sheet.merge_range(row+1, 34, row+2, 34, u'Өртөгийн дүн', format1)

            sheet.merge_range(row, 35, row+2, 35, u'Байвал заохих', format1)

            row +=3

            sheet.merge_range(row,0, row, 4, u'Нийт дүн', format1)
            sum_row = a = 8

            
            row +=1
            j = 0
            get_line = self.get_lines(wiz, warehouse.id, wiz['partner_ids'], wiz['prod_categ_ids'], wiz['product_ids'], wiz['pricelist_id'], warehouse.lot_stock_id.id)
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
                sale_exp = 0
                income_qty = 0
                return_in_value = 0
                if each['purchase_value'] > 0:
                    income_qty += each['purchase_value']
                sheet.write(row, 8, income_qty, font_size_8)
                sheet.write(row, 9, income_qty * each['sale_price'], font_size_8)
                sheet.write(row, 10, income_qty * each['cost_price'], font_size_8)
                
                sheet.write(row, 11, each['trans_in_value'], font_size_8)
                sheet.write(row, 12, each['trans_in_value'] * each['sale_price'], font_size_8)
                sheet.write(row, 13, each['trans_in_value'] * each['cost_price'], font_size_8)


                sheet.write(row, 14, each['inv_in_value'], font_size_8)
                sheet.write(row, 15, each['inv_in_value'] * each['sale_price'], font_size_8)
                sheet.write(row, 16, each['inv_in_value'] * each['cost_price'], font_size_8)

                if each['sale_return_value']>0:
                    return_in_value+= each['sale_return_value']
                if each['pos_return_value']>0:
                    return_in_value+= each['pos_return_value']


                sheet.write(row, 17, return_in_value, font_size_8)
                sheet.write(row, 18, return_in_value * each['sale_price'], font_size_8)
                sheet.write(row, 19, return_in_value * each['cost_price'], font_size_8)

                if each['pos_sale_value']>0:
                    sale_exp+= each['pos_sale_value']
                if each['sale_value']>0:
                    sale_exp+= each['sale_value']

                sheet.write(row, 20, sale_exp, font_size_8)   
                sheet.write(row, 21, sale_exp * each['sale_price'], font_size_8)
                sheet.write(row, 22, sale_exp * each['cost_price'], font_size_8)

                sheet.write(row, 23, each['trans_out_value'], font_size_8)
                sheet.write(row, 24, each['trans_out_value'] * each['sale_price'], font_size_8)
                sheet.write(row, 25, each['trans_out_value'] * each['cost_price'], font_size_8)

                sheet.write(row, 26, each['inv_out_value'], font_size_8)
                sheet.write(row, 27, each['inv_out_value'] * each['sale_price'], font_size_8)
                sheet.write(row, 28, each['inv_out_value'] * each['cost_price'], font_size_8)

                sheet.write(row, 29, each['purchace_return_value'], font_size_8)
                sheet.write(row, 30, each['purchace_return_value'] * each['sale_price'], font_size_8)
                sheet.write(row, 31, each['purchace_return_value'] * each['cost_price'], font_size_8)


                if each['net_on_hand'] < 0:
                    sheet.write(row, 32, each['net_on_hand'], red_mark)
                    sheet.write(row, 33, each['net_on_hand'] * each['sale_price'], red_mark)
                    sheet.write(row, 34, each['net_on_hand'] * each['cost_price'], font_size_8)
                else:
                    sheet.write(row, 32, each['net_on_hand'], font_size_8)
                    sheet.write(row, 33, each['net_on_hand'] * each['sale_price'], font_size_8)
                    sheet.write(row, 34, each['net_on_hand'] * each['cost_price'], font_size_8)

                sheet.write_formula(row, 35, 'SUM(F%s+I%s+L%s+O%s-U%s-X%s-AA%s-AD%s)'%(row+1,row+1,row+1,row+1,row+1,row+1,row+1,row+1), font_size_8)
                row +=1
            a = row
            sheet.write_formula(sum_row, 5, 'SUM(F10:F%s)'%a, format1)
            sheet.write_formula(sum_row, 6, 'SUM(G10:G%s)'%a, format1)
            sheet.write_formula(sum_row, 7, 'SUM(H10:H%s)'%a, format1)
            sheet.write_formula(sum_row, 8, 'SUM(I10:I%s)'%a, format1)
            sheet.write_formula(sum_row, 9, 'SUM(J10:J%s)'%a, format1)
            sheet.write_formula(sum_row, 10, 'SUM(K10:K%s)'%a, format1)
            sheet.write_formula(sum_row, 11, 'SUM(L10:L%s)'%a, format1)
            sheet.write_formula(sum_row, 12, 'SUM(M10:M%s)'%a, format1)
            sheet.write_formula(sum_row, 13, 'SUM(N10:N%s)'%a, format1)
            sheet.write_formula(sum_row, 14, 'SUM(O10:O%s)'%a, format1)
            sheet.write_formula(sum_row, 15, 'SUM(P10:P%s)'%a, format1)
            sheet.write_formula(sum_row, 16, 'SUM(Q10:Q%s)'%a, format1)
            sheet.write_formula(sum_row, 17, 'SUM(R10:R%s)'%a, format1)
            sheet.write_formula(sum_row, 18, 'SUM(S10:S%s)'%a, format1)
            sheet.write_formula(sum_row, 19, 'SUM(T10:T%s)'%a, format1)
            sheet.write_formula(sum_row, 20, 'SUM(U10:U%s)'%a, format1)
            sheet.write_formula(sum_row, 21, 'SUM(V10:V%s)'%a, format1)
            sheet.write_formula(sum_row, 22, 'SUM(W10:W%s)'%a, format1)
            sheet.write_formula(sum_row, 23, 'SUM(X10:X%s)'%a, format1)
            sheet.write_formula(sum_row, 24, 'SUM(Y10:Y%s)'%a, format1)
            sheet.write_formula(sum_row, 25, 'SUM(Z10:Z%s)'%a, format1)
            sheet.write_formula(sum_row, 26, 'SUM(AA10:AA%s)'%a, format1)
            sheet.write_formula(sum_row, 27, 'SUM(AB10:AB%s)'%a, format1)
            sheet.write_formula(sum_row, 28, 'SUM(AC10:AC%s)'%a, format1)
            sheet.write_formula(sum_row, 29, 'SUM(AD10:AD%s)'%a, format1)
            sheet.write_formula(sum_row, 30, 'SUM(AE10:AE%s)'%a, format1)
            sheet.write_formula(sum_row, 31, 'SUM(AF10:AF%s)'%a, format1)
            sheet.write_formula(sum_row, 32, 'SUM(AG10:AG%s)'%a, format1)
            sheet.write_formula(sum_row, 33, 'SUM(AH10:AH%s)'%a, format1)
            sheet.write_formula(sum_row, 34, 'SUM(AI10:AI%s)'%a, format1)
            sheet.write_formula(sum_row, 35, 'SUM(AJ10:AJ%s)'%a, format1)

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

