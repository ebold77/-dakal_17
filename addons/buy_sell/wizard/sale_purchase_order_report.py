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


class SalePurchaseOrderReport(models.TransientModel):
    _name = 'sale.purchase.order.report'
    _description = 'Generate XLSX report for sale purchase order between 2 dates'

    start_date = fields.Date(
        string='Start Date', required=True,
        default=date.today()
        )
    end_date = fields.Date(
        string='End Date',
        default=date.today())

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    
    # def export_xls(self):
    #     data = {
    #         'ids': self.ids,
    #         'model': self._name,
    #         'start_date': self.start_date,
    #         'end_date': self.end_date,

    #     }
    #     return {
    #         'type': 'ir.actions.report',
    #         'data': {'model': 'sale.purchase.order.report',
    #                  'options': json.dumps(data, default=date_utils.json_default),
    #                  'output_format': 'xlsx',
    #                  'report_name': 'SPO report',
    #                  },
    #         'report_type': 'xlsx'
    #     }


    def get_lines(self, data):
        lines = []
        
        start_date =  data['start_date'].strftime("%Y-%m-%d") + ' 00:00:00'
        end_date =  data['end_date'].strftime("%Y-%m-%d") + ' 23:59:59'
        
        self._cr.execute("""SELECT spo.id, partner.name as partner_name, spo.date_order, s_o.name as sale_ref, sum(out_line.product_qty) AS out_qty, \
            sum(out_line.bs_price_total) AS out_barter_price, sum(out_line.list_price_total) AS out_list_price, \
            sum(out_line.discount_total) AS out_discount, sum(out_line.list_price * out_line.product_qty) AS out_base_price \
            FROM buy_sell_order AS spo \
            LEFT JOIN sale_order AS s_o ON spo.sale_order_id = s_o.id \
            LEFT JOIN purchase_order AS p_o ON spo.purchase_order_id = p_o.id \
            LEFT JOIN buy_sell_in_line AS in_line ON in_line.order_id = spo.id \
            LEFT JOIN buy_sell_out_line AS out_line ON out_line.order_id = spo.id \
            LEFT JOIN res_partner AS partner ON partner.id = spo.partner_id \
            WHERE spo.date_order > %s AND spo.date_order <=%s   GROUP BY spo.id, partner.name, s_o.name\
        """, (start_date, end_date))
        spo_query_obj = self._cr.dictfetchall()
       
        for spo_val in spo_query_obj:
            vals = {
            'id': spo_val['id'],
            'partner_name': spo_val['partner_name'],
            'date_order': spo_val['date_order'],
            'sale_ref': spo_val['sale_ref'],
            'out_qty': spo_val['out_qty'],
            'out_base_price': spo_val['out_base_price'],
            'out_barter_price': spo_val['out_barter_price'],
            'out_discount': spo_val['out_discount'],
            'out_list_price': spo_val['out_list_price'],
            }
            lines.append(vals)
        return lines

    def get_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wiz = self.read()[0]
        print('wiz=======================', wiz)
        # lines = self.browse(wiz['ids'])
     
        comp = self.env.user.company_id.name
        report_name = 'Buy Sell Ledger Report'
        filename = report_name
        
        sheet = workbook.add_worksheet('Barter')
        sheet.set_landscape()
        format0 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format1 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'border': 1, 'bold': True, 'text_wrap': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center', 'border': 1})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.merge_range(0, 1, 0, 10, u'Байгууллагын нэр: %s' %comp, format0)
        sheet.merge_range(1, 1, 1, 10, u'Худалдах худалдан авалтын товчоо тайлан', format0)
        sheet.merge_range(2, 1, 2, 10, u'Эхлэх огноо: %s' %wiz['start_date'], format0)
        sheet.merge_range(3, 1, 3, 10, u'Дуусах огноо: %s' %wiz['end_date'], format0)
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else 'UTC')
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        # sheet.merge_range('A8:G8', u'Тайлан хэвлэсэн: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
        row = 5
        sheet.set_column(0, 0, 2)
        sheet.set_column(2, 2, 20)
        sheet.set_row(row+1, 50)
        sheet.merge_range(row,0, row+1, 0, u'№', format1)
        sheet.merge_range(row,1, row+1, 1, u'Огноо', format1)
        sheet.merge_range(row,2, row+1, 2, u'Харилцагч', format1)
        sheet.merge_range(row,3, row, 10, u'Борлуулалт', format1)
        sheet.write(row+1, 3, u'Борлуулалтын №', format1)
        sheet.write(row+1, 4, u'Хүргэх захиалга №', format1)
        sheet.write(row+1, 5, u'Тоо ширхэг', format1)
        sheet.write(row+1, 6, u'Суурь үнэ', format1)
        sheet.write(row+1, 7, u'Бартер үнэ', format1)
        sheet.write(row+1, 8, u'Бартер суурь үнийн зөрүү', format1)
        sheet.write(row+1, 9, u'Боломжит хөнгөлөлт', format1)
        sheet.write(row+1, 10, u'Цэвэр борлуулах үнэ', format1)
        sheet.merge_range(row,11, row, 18, u'Худалдан авалт', format1)
        sheet.write(row+1, 11, u'Худалдан авалт №', format1)
        sheet.write(row+1, 12, u'Ирэх баримт №', format1)
        sheet.write(row+1, 13, u'Тоо ширхэг', format1)
        sheet.write(row+1, 14, u'Суурь үнэ', format1)
        sheet.write(row+1, 15, u'Бартер үнэ', format1)
        sheet.write(row+1, 16, u'Бартер суурь үнийн зөрүү', format1)
        sheet.write(row+1, 17, u'Боломжит хөнгөлөлт', format1)
        sheet.write(row+1, 18, u'Цэвэр борлуулах үнэ', format1)
        sheet.merge_range(row,19, row+1, 19, u'Бартерийн боломжит ашиг', format1)
        row +=2
        # get_line = self.get_lines(wiz)

        start_date =  wiz['start_date'].strftime("%Y-%m-%d") + ' 00:00:00'
        end_date =  wiz['end_date'].strftime("%Y-%m-%d") + ' 23:59:59'

        spo_obj = self.env['buy.sell.order'].search([('date_order', '>=', start_date),
                                                    ('date_order','<=', end_date),
                                                    ('state', 'in',['approved','received','delivered'])])

        i = 1
        sale_pick = purchase_pick = False

        for line in spo_obj:
           
            for pick in line.sale_order_id.picking_ids:
                if pick.picking_type_id.code == 'outgoing':
                    sale_pick = pick
                   
            for pick in line.purchase_order_id.picking_ids:
                if pick.picking_type_id.code == 'incoming':
                    purchase_pick = pick

            if sale_pick.state =='done' and purchase_pick.state =='done':

                out_barter_price = out_discount = out_list_price =  out_base_price = out_qty = 0
                for ol in line.sell_order_line:
                    out_qty += ol.product_qty
                    out_discount += ol.discount_total
                    out_list_price += ol.list_price_total
                    out_barter_price += ol.bs_price_total
                    out_base_price += ol.product_qty * ol.list_price

                in_barter_price = in_discount = in_list_price =  in_base_price = in_qty = 0
                for il in line.buy_order_line:
                    in_qty += il.product_qty
                    in_discount += il.discount_total
                    in_list_price += il.list_price_total
                    in_barter_price += il.bs_price_total
                    in_base_price += il.product_qty * il.list_price

                sheet.write(row, 0, i, font_size_8)
                sheet.write(row, 1, str(line.date_order.strftime("%Y-%m-%d")), font_size_8)
                sheet.write(row, 2, line.partner_id.name, font_size_8)
                sheet.write(row, 3, line.sale_order_id.name, font_size_8)
                sheet.write(row, 4, sale_pick.name, font_size_8)
                sheet.write(row, 5, out_qty, font_size_8)
                sheet.write(row, 6, out_base_price, font_size_8)
                sheet.write(row, 7, out_barter_price, font_size_8)
                sheet.write(row, 8, out_barter_price - out_base_price, font_size_8)
                sheet.write(row, 9, out_discount, font_size_8)
                sheet.write(row, 10, out_list_price, font_size_8)
                sheet.write(row, 11, line.purchase_order_id.name, font_size_8)
                sheet.write(row, 12, purchase_pick.name, font_size_8)
                sheet.write(row, 13, in_qty, font_size_8)
                sheet.write(row, 14, in_base_price, font_size_8)
                sheet.write(row, 15, in_barter_price, font_size_8)
                sheet.write(row, 16, in_barter_price - in_base_price, font_size_8)
                sheet.write(row, 17, in_discount, font_size_8)
                sheet.write(row, 18, in_list_price, font_size_8)
                sheet.write(row, 19, in_list_price - out_list_price, font_size_8)
            # sheet.write(row, 0, i, font_size_8)
            # sheet.write(row, 1, line['date_order'], font_size_8)
            # sheet.write(row, 2, line['partner_name'], font_size_8)
            # sheet.write(row, 3, line['sale_ref'], font_size_8)
            # sheet.write(row, 4, line['sale_ref'], font_size_8)
            # sheet.write(row, 5, line['out_qty'], font_size_8)
            # sheet.write(row, 6, line['out_base_price'], font_size_8)
            # sheet.write(row, 7, line['out_barter_price'], font_size_8)
            # sheet.write(row, 8, line['out_barter_price'] - line['out_base_price'], font_size_8)
            # sheet.write(row, 9, line['out_discount'], font_size_8)
            # sheet.write(row, 10, line['out_barter_price'], font_size_8)
            
            i +=1
            row +=1
        sheet.merge_range(row,0, row, 4, u'Нийт дүн', format1)
        a = row-1

        sheet.write_formula(row, 5, 'SUM(F8:F%s)'%row, format1)
        sheet.write_formula(row, 6, 'SUM(G8:G%s)'%row, format1)
        sheet.write_formula(row, 7, 'SUM(H8:H%s)'%row, format1)
        sheet.write_formula(row, 8, 'SUM(I8:I%s)'%row, format1)
        sheet.write_formula(row, 9, 'SUM(J8:J%s)'%row, format1)
        sheet.write_formula(row, 10, 'SUM(K8:K%s)'%row, format1)
        sheet.write(row, 11, '', format1)
        sheet.write(row, 12, '', format1)
        sheet.write_formula(row, 13, 'SUM(N8:N%s)'%row, format1)
        sheet.write_formula(row, 14, 'SUM(O8:O%s)'%row, format1)
        sheet.write_formula(row, 15, 'SUM(P8:P%s)'%row, format1)
        sheet.write_formula(row, 16, 'SUM(Q8:Q%s)'%row, format1)
        sheet.write_formula(row, 17, 'SUM(R8:R%s)'%row, format1)
        sheet.write_formula(row, 18, 'SUM(S8:S%s)'%row, format1)
        sheet.write_formula(row, 19, 'SUM(T8:T%s)'%row, format1)

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
