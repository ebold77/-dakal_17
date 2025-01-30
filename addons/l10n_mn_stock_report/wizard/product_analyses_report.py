# -*- coding: utf-8 -*-
import time
from datetime import date, datetime
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


class ReportProductAnalyses(models.TransientModel):
    _name = 'report.product.analyses'
    # _inherit = 'abstract.report.model'
    _description = 'Report Product Analyses'
    

    
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    warehouse_ids = fields.Many2many('stock.warehouse', 'report_product_analyses_warehouse_rel',
                            'wizard_id', 'warehouse_id', 'Warehouse')
    product_ids = fields.Many2many('product.product', 'report_product_analyses_product_rel',
                            'wizard_id', 'product_id', 'Product')
    category_ids =   fields.Many2many('product.category', 'report_product_analyses_category_rel',
                            'wizard_id', 'category_id', 'Partner')
    date_to =    fields.Date('To Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_from =  fields.Date('From Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    
    
    def get_log_message(self, ids, context=None):
        form = self.browse(ids[0])
        wnames = ''
        for w in form.warehouse_ids:
            wnames += w.name
            wnames += ','
        body = (u"Орлогын товчоо тайлан (Эхлэх='%s', Дуусах='%s', Салбар=%s)") % \
          (form.date_from, form.date_to, wnames)
        return body


    def export_report_xls(self):
       
        data = {
            'ids': self.ids,
            'model': self._name,
            'start_date': self.date_from,
            'end_date': self.date_to,
             }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'report.product.analyses',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Бараа материалын шинжилгээ тайлан',
                     },
            'report_type': 'xlsx'
        }

    def get_lines(self, data, warehouse, category_ids, product_ids, location_id):
        lines = []
        start_date =  data['start_date'] + ' 00:00:00'
        end_date =  data['end_date'] + ' 23:59:59'
   
        if category_ids:
            categ_products = self.env['product.product'].search([('categ_id', 'in', category_ids.ids)])

        else:
            categ_products = self.env['product.product'].search([])
        product_ids = tuple([pro_id.id for pro_id in categ_products])
       
        sale_query = """
               SELECT sum(s_o_l.qty_delivered) AS qty_delivered, sum(s_o_l.product_uom_qty) AS product_uom_qty, s_o_l.product_id FROM sale_order_line AS s_o_l
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
               SELECT sum(sm_l.qty_done) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_inventory AS s_i ON s_m.inventory_id = s_i.id
               WHERE s_i.state = 'done' 
               AND s_i.date >= %s
               AND s_i.date <= %s
               AND s_m.location_dest_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        inventory_expense_query = """
               SELECT sum(sm_l.qty_done) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_inventory AS s_i ON s_m.inventory_id = s_i.id
               WHERE s_i.state = 'done' 
               AND s_i.date >= %s
               AND s_i.date <= %s
               AND s_m.location_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        transit_income_query = """
               SELECT sum(sm_l.qty_done) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='transit'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_dest_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        transit_out_query = """
               SELECT sum(sm_l.qty_done) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_dest_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='transit'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        return_in_query = """
               SELECT sum(sm_l.qty_done) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
               JOIN stock_move AS s_m ON s_m.id = sm_l.move_id
               JOIN stock_location AS s_l ON s_m.location_id = s_l.id
               WHERE s_m.state = 'done'
               AND s_l.usage='customer'
               AND s_m.date >= %s
               AND s_m.date <= %s
               AND s_m.location_dest_id = %s
               AND s_m.product_id in %s group by sm_l.product_id;"""

        return_out_query = """
               SELECT sum(sm_l.qty_done) AS product_qty, sm_l.product_id FROM stock_move_line AS sm_l
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
            sale_return_value = qty_delivered = sale_value = 0
            purchace_return_value = purchase_value = 0
            pos_return_value = pos_sale_value = 0
            inv_out_value = inv_in_value = 0
            trans_in_value = trans_out_value = 0
            # sale_price = pricelist_id.get_product_price(obj , 1, 1)
            for sol_product in sol_query_obj:
                if sol_product['product_id'] == obj.id:
                    sale_value = sol_product['product_uom_qty']
                    qty_delivered = sol_product['qty_delivered']

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
                sale_return_value != 0 or pos_return_value != 0 or \
                inv_out_value !=0 or inv_in_value !=0:
                vals = {
                    'default_code': obj.default_code,
                    'bar_code': obj.barcode,
                    'name': obj.name,
                    'uom': obj.uom_id.name,
                    'category': obj.categ_id.name,
                    # 'cost_price': obj.standard_price,
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
                    'qty_delivered': qty_delivered,
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

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.browse(data['ids'])
        
        comp = self.env.user.company_id.name
        
        format0 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format1 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'border': 1, 'bold': True, 'text_wrap': True, 'bg_color': '33DDFF'})
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

        
        for warehouse in wiz.warehouse_ids:
            
            sheet = workbook.add_worksheet(warehouse.name)
            sheet.set_landscape()
            sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
            sheet.merge_range(1, 1, 1, 10, u'Бараа материалын шинжилгээ', format0)
            sheet.merge_range(2, 1, 2, 10, u'Эхлэх огноо: %s' %data['start_date'], format0)
            sheet.merge_range(3, 1, 3, 10, u'Дуусах огноо: %s' %data['end_date'], format0)
            user = self.env['res.users'].browse(self.env.uid)
            tz = pytz.timezone(user.tz if user.tz else 'UTC')
            times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
            # sheet.merge_range('A8:G8', u'Тайлан хэвлэсэн: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
            row = 5
            sheet.set_column(0, 0, 2)
            sheet.set_column(2, 3, 10)
            sheet.set_column(4, 4, 30)
            sheet.set_row(row, 50)
            sheet.write(row, 0, u'№', format1)
            sheet.write(row, 1, u'Дотоод код', format1)
            sheet.write(row, 2, u'Бар код', format1)
            sheet.write(row, 3, u'Барааны ангилал', format1)
            sheet.write(row, 4, u'Бараа материал', format1)
            sheet.write(row, 5, u'Эхний үлдэгдэл', format1)

            sheet.write(row, 6, u'Орлого', format1)
            sheet.write(row, 7, u'Захаилсан тоо', format1)
            sheet.write(row, 8, u'Хүргэсэн тоо', format1)
            sheet.write(row, 9, u'Буцаалт', format1)
            sheet.write(row, 10, u'Дотоод шилжүүлэлт', format1)
            sheet.write(row, 11, u'Эцсийн үлдэгдэл', format1)
            # sheet.write(row, 11, u'НӨАТ-гүй дүн', format1)
            # sheet.write(row, 6, u'Өртөгийн дүн', format1)

            
            row +=1
            j = 0
            get_line = self.get_lines(data, warehouse.id, wiz.category_ids, wiz.product_ids,warehouse.lot_stock_id.id)

            for each in get_line:
                j += 1
                income_qty = 0
                return_in_value = 0
                sheet.write(row, 0, j, font_size_8)
                sheet.write(row, 1, each['default_code'], font_size_8)
                sheet.write(row, 2,each['bar_code'], font_size_8_l_b)
                sheet.write(row, 3, each['category'], font_size_8)
                sheet.write(row, 4, each['name'], font_size_8_l_b)
                if each['initial_balance'] < 0:
                    sheet.write(row, 5, each['initial_balance'], red_mark)
                else:
                    sheet.write(row, 5, each['initial_balance'], font_size_8)
                
                # if each['purchase_value'] > 0:
                income_qty += each['purchase_value'] + each['trans_in_value']
                sheet.write(row, 6, income_qty, font_size_8)
                sheet.write(row, 7, each['sale_value'] + each['pos_sale_value'], font_size_8)
                sheet.write(row, 8, each['qty_delivered'] + each['pos_sale_value'], font_size_8)
                if each['sale_return_value']>0:
                    return_in_value+= each['sale_return_value']
                if each['pos_return_value']>0:
                    return_in_value+= each['pos_return_value']


                sheet.write(row, 9, return_in_value, font_size_8)
                sheet.write(row, 10, each['trans_out_value'], font_size_8)
                if each['net_on_hand'] < 0:
                    sheet.write(row, 11, each['net_on_hand'], red_mark)
                else:
                    sheet.write(row, 11, each['net_on_hand'], font_size_8)
                row +=1
            #     sheet.write(sum_row, 5, total_qty, format1)
            #     sheet.write(sum_row, 6, total_cost, format1)

            sheet.merge_range(row+1, 2, row+1, 8, u'Нягтлан бодогч .................................. (                                   )', font_size_8_l)
            sheet.merge_range(row+3, 2, row+3, 8, u'Эд хариуцагч  .................................. (                                   )' , font_size_8_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
    
