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


class ReportExpenseLedger(models.TransientModel):
    _name = 'report.expense.ledger'
    # _inherit = 'abstract.report.model'
    _description = 'Report Expense Ledger'
    
    # def _get_pos_install(self):
    #     '''
    #         Посын модуль суусан эсэхийг шалгана.
    #     '''
    #     pos_obj = self.env['ir.module.module'].search([('state','=','installed'), ('name','=','point_of_sale')]) 
    #     if pos_obj:
    #         return True
    #     return False
    
    # def _get_mrp_install(self):
    #     '''
    #         Үйлдвэрлэлийн модуль суусан эсэхийг шалгана.
    #     '''
    #     mrp_obj = self.env['ir.module.module'].search([('state','=','installed'), ('name','=','mrp')]) 
    #     if mrp_obj:
    #         return True
    #     return False

    
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    warehouse_ids = fields.Many2many('stock.warehouse', 'report_expense_ledger_warehouse_rel',
                            'wizard_id', 'warehouse_id', 'Warehouse')
    product_ids = fields.Many2many('product.product', 'report_expense_ledger_product_rel',
                            'wizard_id', 'product_id', 'Product')
    partner_ids =   fields.Many2many('res.partner', 'report_expense_ledger_partner_rel',
                            'wizard_id', 'partner_id', 'Partner')
    category_ids =   fields.Many2many('product.category', 'report_expense_ledger_category_rel',
                            'wizard_id', 'category_id', 'Partner')
    date_to =    fields.Date('To Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_from =  fields.Date('From Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    sales =      fields.Boolean('Sales', default = True)
    refund =     fields.Boolean('Refund', default = True)
    procure =    fields.Boolean('Replenishment', default = True)
    swap =       fields.Boolean('Swap', default = True)
    inventory =  fields.Boolean('Inventory', default = True)
    pos =        fields.Boolean('Pos Sale', default = True)
    mrp =        fields.Boolean('MRP Production', default = True)
    consume =    fields.Boolean('Internal Expense', default = True)
    report_type =       fields.Selection([('detail','Detail'),('summary','Summary')], 'report_type', default='summary', required=True)
    cost =       fields.Boolean('Show Cost Amount?', default = True)
    # pos_install =   fields.Boolean('Pos Install', default=_get_pos_install)
    # mrp_install =   fields.Boolean('MRP Install', default=_get_mrp_install)
        
    
    def get_log_message(self, ids, context=None):
        form = self.browse(ids[0])
        wnames = ''
        for w in form.warehouse_ids:
            wnames += w.name
            wnames += ','
        body = (u"Зарлагын товчоо тайлан (Эхлэх='%s', Дуусах='%s', Салбар=%s)") % \
          (form.date_from, form.date_to, wnames)
        return body


    # def export_report_xls(self):
       
    #     data = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'start_date': self.date_from,
    #         'end_date': self.date_to,
    #         'report_type': self.report_type,
    #         'pos': self.pos,
    #         'procure': self.procure,
    #         'refund': self.refund,
    #         'inventory': self.inventory,
    #         'purchase': self.pos,
    #          }
    #     return {
    #         'type': 'ir.actions.report',
    #         'data': {'model': 'report.expense.ledger',
    #                  'options': json.dumps(data, default=date_utils.json_default),
    #                  'output_format': 'xlsx',
    #                  'report_name': 'Зарлагын товчоо тайлан',
    #                  },
    #         'report_type': 'xlsx'
    #     }

    def get_lines(self, data, picking_type_id):
        lines = []
        start_date =  data['date_from'].strftime("%Y-%m-%d") + ' 00:00:00'
        end_date =  data['date_to'].strftime("%Y-%m-%d") + ' 23:59:59'
        res = {}
        name_dict = {}
        cost_dict = {}
        cost_list = []

        expense_query = """
               SELECT sp.id as picking_id, sp.sale_id as sale_id, sp.transit_order_id as transit_order_id, sp.date_done as date_done, sp.name as name, sp.origin as origin, 
               sp.partner_id as partner_name, sum(sm_l.quantity) AS product_qty, sum(sm.price_unit * sm_l.quantity) as cost_amount 
               FROM stock_picking AS sp
               JOIN stock_move_line AS sm_l ON sm_l.picking_id = sp.id
               JOIN stock_move AS sm ON sm_l.move_id = sm.id
               WHERE sp.state = 'done' 
               AND sp.picking_type_id = %s
               AND sp.date_done >= %s
               AND sp.date_done <= %s group by sp.id, sp.name, sp.origin order by sp.date_done ;"""

       


        params = picking_type_id, start_date, end_date
        self._cr.execute(expense_query, params)
        expense_query_obj = self._cr.dictfetchall()
        where = ''
        group_by = ''
        select_type = ''
        self._cr.execute("SELECT cast(m.date as date) AS date, m.id AS move_id, m.origin_returned_move_id AS return_id, rp.id as partner_name, "
                            "m.product_id AS prod_id, p.name as name, p.origin as origin,"
                            "(CASE WHEN m.purchase_line_id is not null THEN 'purchase' "
                                "WHEN m.picking_id is not null and p.transit_order_id is not null THEN 'procure' "+select_type+" "
                                "WHEN m.orderpoint_id is not null THEN 'procure' "
                                "WHEN m.origin_returned_move_id is not null THEN 'refund' ELSE 'pos' END) AS rep_type, "
                            "SUM(sm_l.quantity) AS qty, "
                            "SUM(coalesce((m.price_unit * sm_l.quantity),0)) AS cost, "
                            "SUM(coalesce((m.price_unit * sm_l.quantity),0)) AS amount "
                        "FROM stock_move AS m "
                            "LEFT JOIN stock_picking AS p ON (m.picking_id = p.id) "
                            "JOIN stock_move_line AS sm_l ON sm_l.move_id = m.id "
                            "LEFT JOIN res_partner AS rp ON (p.partner_id = rp.id) "
                            "JOIN product_product AS pp ON (m.product_id = pp.id) "
                            "JOIN product_template AS pt ON (pp.product_tmpl_id = pt.id) " 
                        "WHERE p.picking_type_id= %s "
                            "AND m.state = 'done' "
                            "AND m.date >= %s AND m.date <= %s "+where+" "
                        "GROUP BY m.id,m.date,m.origin_returned_move_id,m.picking_id,rp.id,m.purchase_line_id, "+group_by+" "
                            "p.name,m.product_id,p.origin,p.transit_order_id "
                        "ORDER BY m.date "
                            ,(picking_type_id, start_date, end_date))
        result = self._cr.dictfetchall()

        product_obj = self.env['product.product']
        prod_ids = []
        def _cost_get(d):
            cost = d.get('price_unit', 0)      
            return (d['id'], cost)

        # if data['report_type'] == 'detail':
        for r in result:
            if r['prod_id'] not in prod_ids:
                prod_ids.append(r['prod_id'])
        if prod_ids:
            for prod in product_obj.search([('id', 'in', prod_ids)]):
                name_dict = dict( prod.name_get())
                mydict = {
                      'id': prod.id,
                      'price_unit': prod.standard_price,
                      }
                temp = _cost_get(mydict)
                cost_list.append(temp)
                cost_dict = dict(cost_list)
            
        for r in result:
            tax = taxed = 0
            if r['rep_type'] == 'pos' and  not data['pos']:
                continue
            if r['rep_type'] == 'procure' and not data['procure']:
                continue
            if r['rep_type'] == 'refund' and not data['refund']:
                continue
            # if r['rep_type'] == 'inventory' and not data['inventory']:
            #     continue
            if r['rep_type'] == 'purchase' and not data['purchase']:
                continue
            # if r['rep_type'] in ('purchase','pos'):
            #     if r['rep_type'] == 'pos':
            #         taxed = round(float(r['amount'])/float(1+float(TAX_FACTOR)),4)
            #         tax = r['amount'] - taxed
            #     else:
            #         if r['tax'] > 0:
            #             taxed = round(float(r['amount'])/float(1+float(TAX_FACTOR)),4)
            #             tax = r['amount'] - taxed
            
            if r['rep_type'] not in res:
                res[r['rep_type']] = {'name': r['rep_type'],
                                      'lines': {},
                                      'total': 0,
                                      'qty': 0,
                                      'taxed': 0,
                                      'tax': 0,
                                      'cost':0}
            if r['cost'] == 0:
                r['cost'] = float(cost_dict.get(r['prod_id'],0)) * r['qty']

            res[r['rep_type']]['qty'] += r['qty']
            res[r['rep_type']]['total'] += r['amount']
            res[r['rep_type']]['cost'] += r['cost']
            res[r['rep_type']]['tax'] += tax
            res[r['rep_type']]['taxed'] += taxed

            if r['name'] not in res[r['rep_type']]['lines']:
                res[r['rep_type']]['lines'][r['name']] = {'date': r['date'],
                                                          'name': r['name'] or '',
                                                          'origin': r['origin'] or '',
                                                          'partner': r['partner_name'] or '',
                                                          'total': 0,
                                                          'qty': 0,
                                                          'taxed': 0,
                                                          'tax': 0,
                                                          'cost':0,
                                                          'lines':{}}
            res[r['rep_type']]['lines'][r['name']]['qty'] += r['qty']
            res[r['rep_type']]['lines'][r['name']]['total'] += r['amount']
            res[r['rep_type']]['lines'][r['name']]['cost'] += r['cost']
            res[r['rep_type']]['lines'][r['name']]['tax'] += tax
            res[r['rep_type']]['lines'][r['name']]['taxed'] += taxed
            if data['report_type'] == 'detail':
                if r['prod_id'] not in res[r['rep_type']]['lines'][r['name']]['lines']:
                    res[r['rep_type']]['lines'][r['name']]['lines'][r['prod_id']] = {'date': '',
                                                                                     'name': name_dict.get(r['prod_id'],''),
                                                                                     'origin': '',
                                                                                     'partner': '',
                                                                                     'total': 0,
                                                                                     'qty': 0,
                                                                                     'taxed': 0,
                                                                                     'tax': 0,
                                                                                     'cost':0}
                res[r['rep_type']]['lines'][r['name']]['lines'][r['prod_id']]['qty'] += r['qty']
                res[r['rep_type']]['lines'][r['name']]['lines'][r['prod_id']]['total'] += r['amount']
                res[r['rep_type']]['lines'][r['name']]['lines'][r['prod_id']]['cost'] += r['cost']
                res[r['rep_type']]['lines'][r['name']]['lines'][r['prod_id']]['tax'] += tax
                res[r['rep_type']]['lines'][r['name']]['lines'][r['prod_id']]['taxed'] += taxed

        # for expense in expense_query_obj:
        #     if expense:
        #         partner_name = ''
        #         price_tax = discount = 0
        #         cost_amount = listprice_ammount =0
        #         price_subtotal = price_total = 0
        #         if expense['partner_name']:
        #             partner = self.env['res.partner'].search([('id', '=', expense['partner_name'])])
        #             partner_name = partner.name
        #         if expense['sale_id']:

        #             price_query = """
        #                 SELECT sp.id as picking_id, sum(sol.price_total* sol.discount/100) as discount, sum(sol.price_unit * sm_l.quantity) as listprice_ammount, 
        #                 sum(sol.price_tax) as price_tax, sum(sol.price_subtotal) as price_subtotal, 
        #                 sum(sol.price_total) as price_total, sum(svl.value) as cost_amount 
        #                FROM stock_picking AS sp
        #                JOIN stock_move_line AS sm_l ON sm_l.picking_id = sp.id
        #                JOIN stock_move AS sm ON sm_l.move_id = sm.id
        #                JOIN sale_order_line AS sol ON sol.id = sm.sale_line_id
        #                JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
        #                WHERE sp.id = %s 
        #                AND sol.order_id = %s group by sp.id
        #               """
        #             params = expense['picking_id'], expense['sale_id']

        #             self._cr.execute(price_query, params)
        #             price_query_obj = self._cr.dictfetchone()
        #             if price_query_obj:
        #                 listprice_ammount = price_query_obj['listprice_ammount']
        #                 discount = price_query_obj['discount']
        #                 price_total = price_query_obj['price_total']
        #                 price_tax = price_query_obj['price_tax']
        #                 price_subtotal = price_query_obj['price_subtotal']
        #                 cost_amount = price_query_obj['cost_amount'] *-1
        #         else:
        #             cost_amount = expense['cost_amount']
        #         vals = {
        #             'date_done': expense['date_done'].strftime('%Y-%m-%d'),
        #             'name': expense['name'],
        #             'origin': expense['origin'],
        #             'partner_name': partner_name,
        #             'qty': expense['product_qty'],
        #             'picking_id': expense['picking_id'],
        #             'sale_id': expense['sale_id'],
        #             'transit_order_id': expense['transit_order_id'],
        #             'list_price': listprice_ammount,
        #             'discount': discount,
        #             'sale_price': price_total,
        #             'amount_tax': price_tax,
        #             'subtotal': price_subtotal,
        #             'cost_amount': cost_amount,
        #         }
        #         lines.append(vals)

        return res

    def get_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.read()[0]
        print('wiz=======================', wiz)
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

        # date_string = self.get_default_date_tz().strftime("%Y-%m-%d")
        report_name = 'Stock Expense Ledger Report'
        filename = report_name

        
        for warehouse_id in wiz['warehouse_ids']:
            warehouse = self.env['stock.warehouse'].browse(warehouse_id)
            sheet = workbook.add_worksheet(warehouse.name)
            sheet.set_landscape()
            sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
            sheet.merge_range(1, 1, 1, 10, u'Зарлагын товчоо тайлан', format0)
            sheet.merge_range(2, 1, 2, 10, u'Эхлэх огноо: %s' %wiz['date_from'], format0)
            sheet.merge_range(3, 1, 3, 10, u'Дуусах огноо: %s' %wiz['date_to'], format0)
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
            sheet.write(row, 1, u'Огноо', format1)
            sheet.write(row, 2, u'Баримтын дугаар', format1)
            sheet.write(row, 3, u'Эх Баримт', format1)
            sheet.write(row, 4, u'Харилцагчийн нэр', format1)

            sheet.write(row, 5, u'Тоо хэмжээ', format1)
            # sheet.write(row, 6, u'Худалдах үнийн дүн', format1)
            # sheet.write(row, 7, u'Нийт дүн', format1)
            # sheet.write(row, 8, u'Хөнгөлөлт', format1)
            # sheet.write(row, 9, u'Цэвэр дүн', format1)
            # sheet.write(row, 10, u'НӨАТ', format1)
            # sheet.write(row, 11, u'НӨАТ-гүй дүн', format1)
            sheet.write(row, 6, u'Өртөгийн дүн', format1)

            
            row +=1
            j = 0
            get_line = self.get_lines(wiz, warehouse.out_type_id.id)
    
            for val in get_line.values():

                name = val['name']
                if val['name'] == 'procure':
                    name = u'Нөхөн дүүргэлт'
                elif val['name'] == 'pos':
                    name = u'Борлуулалт'
                elif val['name'] == 'purchase':
                    name = u'Худалдан авалт'
                elif val['name'] == 'mrp':
                    name = u'Үйлдвэрлэл'
                elif val['name'] == 'swap':
                    name = u'Солилцоо'
                elif val['name'] == 'refund':
                    name = u'Буцаалт'
                # elif val['name'] == 'inventory':
                #     name = u'Тооллого'
                sheet.merge_range(row, 0, row, 4, name, format1)
                sum_row = row
                total_cost = 0
                total_qty = 0
                row +=1
                for v in val['lines'].values():   
                    partner_name = ''
                    if v['partner']:
                        partner = self.env['res.partner'].search([('id', '=', v['partner'])])
                        partner_name = partner.name
                    j += 1
                    sheet.write(row, 0, j, font_size_8)
                    sheet.write(row, 1, v['date'].strftime('%Y-%m-%d'), font_size_8)
                    sheet.write(row, 2,v['name'], font_size_8_l_b)
                    sheet.write(row, 3, v['origin'], font_size_8_l_b)
                    sheet.write(row, 4, partner_name, font_size_8_l_b)
                    sheet.write(row, 5, v['qty'], font_size_8)
                    # sheet.write(row, 6, v['cost'], font_size_8)
                    # sheet.write(row, 7, v['cost'], font_size_8)
                    # sheet.write(row, 8, v['discount'], font_size_8)
                    # sheet.write(row, 9, v['cost'], font_size_8)
                    # sheet.write(row, 10, v['amount_tax'], font_size_8)
                    
                    # sheet.write(row, 11, v['subtotal'], font_size_8)
                    sheet.write(row, 6, v['cost'], font_size_8)
                    total_qty += v['qty']
                    total_cost +=v['cost']
                    row +=1
                sheet.write(sum_row, 5, total_qty, format1)
                sheet.write(sum_row, 6, total_cost, format1)


            sheet.merge_range(row+1, 2, row+1, 8, u'Нягтлан бодогч .................................. (                                   )', font_size_8_l)
            sheet.merge_range(row+3, 2, row+3, 8, u'Эд хариуцагч  .................................. (                                   )' , font_size_8_l)

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
    
