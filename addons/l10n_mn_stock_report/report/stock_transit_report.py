# -*- coding: utf-8 -*-
import time
import xlsxwriter
import base64
from datetime import datetime
from odoo import fields, models, api, _
from odoo.tools.translate import _
from io import BytesIO
from odoo.addons.l10n_mn_web.models.time_helper import *
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles


class StockTransitOrderReport(models.TransientModel):
    _name = "stock.transit.order.report"

    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date(default=fields.Date.context_today)
    transit_order_id = fields.Many2one('stock.transit.order', 'Transit Order')
    transit_order_ids = fields.Many2many('stock.transit.order', 'stock_transit_order_report_rel', 'report_id',
                                         'transit_order_id', 'Transit Orders')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    warehouse_ids = fields.Many2many('stock.warehouse', 'stock_transit_order_warehouse_report_rel2', 'report_id',
                                     'warehouse_id', 'Warehouses')
    in_warehouse_id = fields.Many2one('stock.warehouse', 'In Warehouse')
    in_warehouse_ids = fields.Many2many('stock.warehouse', 'stock_transit_order_in_warehouse_report_rel2', 'report_id',
                                        'in_warehouse_id', 'Warehouses')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    is_residual = fields.Boolean('Is Residual', default=True)

    @api.onchange("company_id")
    def _get_warehouse_and_categ_domain(self):
        domain = {}
        domain['warehouse_ids'] = [('company_id', '=', self.company_id.id)]
        _warehouses = []
        for warehouse in self.env.user.allowed_warehouses:
            _warehouses.append(warehouse.id)
        if _warehouses:
            domain['warehouse_ids'] = [('id', 'in', _warehouses), ('company_id', '=', self.company_id.id)]
            domain['warehouse_ids'] = [('id', 'in', _warehouses), ('company_id', '=', self.company_id.id)]
        return {'domain': domain}

    def get_export_data(self):
        # create workbook
        output = BytesIO()
        book = xlsxwriter.Workbook(output)

        # create name
        report_name = _('Transit order report')
        file_name = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'),)

        # create formats
        format_name = book.add_format(ReportExcelCellStyles.format_name)
        format_filter = book.add_format(ReportExcelCellStyles.format_filter)
        format_title = book.add_format(ReportExcelCellStyles.format_title)
        format_content_text = book.add_format(ReportExcelCellStyles.format_content_text)
        format_content_left_float = book.add_format(ReportExcelCellStyles.format_content_left_float)

        date_from = str(get_day_by_user_timezone(str(self.start_date) + ' 00:00:00', self.env.user))
        date_to = str(get_day_by_user_timezone(str(self.end_date) + ' 23:59:59', self.env.user))

        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=('transit_order_report'), form_title=file_name, date_to=self.end_date, date_from=self.start_date).create({})

        # create sheet
        sheet = book.add_worksheet(report_name)
        sheet.set_landscape()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.78, 0.39, 0.39, 0.39)  # 2cm, 1cm, 1cm, 1cm
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&C&"Times New Roman"&9&P', {'margin': 0.1})
        sheet.merge_range('B2:C2', '%s: %s' % (_('Company'), self.company_id.name), format_filter)
        sheet.merge_range('B3:N3', _('STOCK TRANSIT DETAIL REPORT'), format_name)
        sheet.merge_range('B5:C5', '%s: %s - %s' % (_('Report duration'), date_from, date_to), format_filter)
        sheet.merge_range('B6:C6', '%s: %s' % (_('Create Date'), get_day_like_display(fields.Datetime.now(), self.env.user)), format_filter)
        sheet.merge_range('A8:A9', u'№', format_title)
        sheet.merge_range('B8:B9', _('Order Number'), format_title)
        sheet.merge_range('C8:C9', _('Date'), format_title)
        sheet.merge_range('D8:D9', _('Supply warehouse'), format_title)
        sheet.merge_range('E8:E9', _('Receive warehouse'), format_title)

        out_pick_list = []
        in_pick_list = []
        where = ''
        if self.transit_order_ids:
            where += ' AND st.id IN (' + ','.join(str(elem['id']) for elem in self.transit_order_ids) + ')'
        if self.warehouse_ids:
            where += ' AND sws.id IN (' + ','.join(str(elem['id']) for elem in self.warehouse_ids) + ')'
        if self.in_warehouse_ids:
            where += ' AND sw.id IN (' + ','.join(str(elem['id']) for elem in self.in_warehouse_ids) + ')'

        self.env.cr.execute("SELECT id FROM stock_picking_type WHERE code='outgoing'")
        out_pick_ids = self.env.cr.dictfetchall()
        for out_pick_id in out_pick_ids:
            out_pick_list.append(out_pick_id['id'])
        self.env.cr.execute("select id from stock_picking_type where code='incoming'")
        in_pick_ids = self.env.cr.dictfetchall()
        for in_pick_id in in_pick_ids:
            in_pick_list.append(in_pick_id['id'])
        self.env.cr.execute("SELECT sm.id AS move_id, "
                                "sm.product_id AS move_product_id, "
                                "sm.product_qty AS qty, "
                                "sm.price_unit AS price_unit, "
                                "st.name AS tr_name, "
                                "st.id AS tr_id, "
                                "st.date_order AS tr_date, "
                                "pp.id AS p_id, "
                                "pp.barcode AS p_barcode, "
                                "sp.picking_type_id AS pick_id, "
                                "sp.name AS sp_name, "
                                "tem.name AS prod_name, "
                                "sw.name AS sw_name, "
                                "sws.name AS sws_name "
                            "FROM   stock_move sm "
                                "INNER JOIN stock_picking sp "
                                "ON sm.picking_id = sp.id "
                                "INNER JOIN stock_transit_order st "
                                "ON sp.transit_order_id = st.id "
                                "INNER JOIN stock_warehouse sw "
                                "ON st.warehouse_id = sw.id "
                                "INNER JOIN stock_warehouse sws "
                                "ON st.supply_warehouse_id = sws.id "
                                "INNER JOIN product_product pp "
                                "ON sm.product_id = pp.id "
                                "INNER JOIN product_template tem "
                                "ON tem.id = pp.product_tmpl_id "
                            "WHERE sm.state='done' and st.date_order >=%s and st.date_order<=%s" + where +
                            "ORDER BY st.id, sm.product_id; "
                            , (date_from, date_to))
        result = self.env.cr.dictfetchall()
        result_dict = {}
        qty_dict = {}
        cost_dict = {}
        rowx = 9
        count = 1
        for rs in result:
            if rs['tr_id'] not in result_dict:
                result_dict[rs['tr_id']] = {
                    'tr_id': rs['tr_id'],
                    'name': rs['tr_name'],
                    'date': rs['tr_date'],
                    'swh': rs['sws_name'],
                    'wh': rs['sw_name'],
                    'p_id': rs['p_id']
                }
        for dict in result_dict:
            out_list = []
            in_list = []
            for rs in result:
                if rs['tr_id'] == result_dict[dict]['tr_id']:
                    if rs['tr_id'] not in cost_dict:
                        cost_dict[rs['tr_id']] = {
                            'cost': rs['qty'] * (rs['price_unit'] or 0.0) if rs['pick_id'] in out_pick_list else (-1) * rs['qty'] * (rs['price_unit'] or 0.0)
                        }
                    else:
                        if rs['pick_id'] in out_pick_list:
                            cost_dict[rs['tr_id']]['cost'] += rs['qty'] * (rs['price_unit'] or 0.0)
                        else:
                            if rs['pick_id'] in in_pick_list:
                                cost_dict[rs['tr_id']]['cost'] -= rs['qty'] * (rs['price_unit'] or 0.0)
                    if (rs['tr_id'], rs['move_product_id']) not in qty_dict:
                        qty_dict[rs['tr_id'], rs['move_product_id']] = {
                            'qty': rs['qty'] if rs['pick_id'] in out_pick_list else -rs['qty'],
                            'name': rs['prod_name']}

                    else:
                        if rs['pick_id'] in out_pick_list:
                            qty_dict[rs['tr_id'], rs['move_product_id']]['qty'] += rs['qty']
                        else:
                            if rs['pick_id'] in in_pick_list:
                                qty_dict[rs['tr_id'], rs['move_product_id']]['qty'] -= rs['qty']
                    if rs['pick_id'] in out_pick_list:
                        # Зарлагын тоо хэмжээг 1 мөрөнд гаргах
                        if rs['p_id'] not in (l['product_id'] for l in out_list):
                            out_list.append({
                                'barcode': rs['p_barcode'],
                                'picking_name': rs['sp_name'],
                                'product_name': rs['prod_name'],
                                'product_id': rs['p_id'],
                                'qty': rs['qty'],
                                'price_unit': (rs['price_unit'] or 0.0),
                                'sub_total': rs['qty'] * (rs['price_unit'] or 0.0)
                            })
                        else:
                            for l in out_list:
                                l['qty'] += rs['qty'] if l['product_id'] == rs['p_id'] else 0

                    if rs['pick_id'] in in_pick_list:
                        # Орлогын тоо хэмжээг 1 мөрөнд гаргах
                        if rs['p_id'] not in (l['product_id'] for l in in_list):
                            in_list.append({
                                'picking_name': rs['sp_name'],
                                'product_name': rs['prod_name'],
                                'product_id': rs['p_id'],
                                'qty': rs['qty'],
                                'price_unit': (rs['price_unit'] or 0.0),
                                'sub_total': rs['qty'] * (rs['price_unit'] or 0.0)
                            })
                        else:
                            for l in in_list:
                                l['qty'] += rs['qty'] if l['product_id'] == rs['p_id'] else 0
            result_dict[dict]['out'] = out_list
            result_dict[dict]['in'] = in_list
        for dict in result_dict:
            if not self.is_residual or (self.is_residual and result_dict[dict]['tr_id'] in cost_dict and cost_dict[result_dict[dict]['tr_id']]['cost'] != 0):
                f1_count = 1
                f2_count = 1
                f3_count = 1
                f4_count = 1
                out_count = 1
                in_count = 1

                sheet.write(rowx, 0, str(count), format_content_text)
                sheet.write(rowx, 1, result_dict[dict]['name'], format_content_text)
                warehouse_date = datetime.strptime(str(result_dict[dict]['date']), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                sheet.write(rowx, 2, warehouse_date, format_content_text)
                sheet.write(rowx, 3, result_dict[dict]['swh'], format_content_text)
                sheet.write(rowx, 4, result_dict[dict]['wh'], format_content_text)
                sheet.set_row(rowx, 30)
                rowx += 1
                rowy = rowx
                col = 0

                sum_out_qty = 0
                sum_out_price_unit = 0
                sum_out_sub_total = 0
                sum_in_qty = 0
                sum_in_price_unit = 0
                sum_in_sub_total = 0
                sum_qty_dict_qty = 0
                sheet.merge_range(rowy, col, rowy, col + 6, _('Out'), format_title)
                sheet.write(rowy + f2_count, col, u'№', format_title)
                sheet.write(rowy + f2_count, col + 1, _('Barcode'), format_title)
                sheet.write(rowy + f2_count, col + 2, _('Product'), format_title)
                sheet.write(rowy + f2_count, col + 3, _('Expense receipt number'), format_title)
                sheet.write(rowy + f2_count, col + 4, _('Quantity'), format_title)
                sheet.write(rowy + f2_count, col + 5, _('Price Unit'), format_title)
                sheet.write(rowy + f2_count, col + 6, _('Total Cost'), format_title)
                sheet.set_row(rowy + f2_count, 30)
                f2_count += 1
                out_dictionary = result_dict[result_dict[dict]['tr_id']]['out']
                if not out_dictionary:
                    in_dict_count = result_dict[result_dict[dict]['tr_id']]['in']
                    for obj in in_dict_count:
                        vls = {'barcode': '', 'picking_name': '', 'product_name': obj['product_name'], 'product_id': 0.0, 'qty': 0.0, 'price_unit': 0.0, 'sub_total': 0.0}
                        out_dictionary.append(vls)
                for out_dict in out_dictionary:
                    sheet.set_row(rowy + f2_count, 30)
                    sheet.write(rowy + f2_count, col, str(count) + '/' + str(out_count), format_content_text)
                    sheet.write(rowy + f2_count, col + 1, out_dict['barcode'], format_content_text)
                    sheet.write(rowy + f2_count, col + 2, out_dict['product_name'], format_content_text)
                    sheet.write(rowy + f2_count, col + 3, out_dict['picking_name'], format_content_text)
                    sheet.write(rowy + f2_count, col + 4, out_dict['qty'], format_content_text)
                    sheet.write(rowy + f2_count, col + 5, out_dict['price_unit'], format_content_left_float)
                    sheet.write(rowy + f2_count, col + 6, out_dict['sub_total'], format_content_left_float)

                    sum_out_price_unit += out_dict['price_unit']
                    sum_out_sub_total += out_dict['sub_total']
                    sum_out_qty += out_dict['qty']

                    f2_count += 1
                    out_count += 1

                sheet.merge_range(rowy, col + 7, rowy, col + 10, _('Arrived'), format_title)
                sheet.write(rowy + f3_count, col + 7, _('Income document number'), format_title)
                sheet.write(rowy + f3_count, col + 8, _('Quantity'), format_title)
                sheet.write(rowy + f3_count, col + 9, _('Price Unit'), format_title)
                sheet.write(rowy + f3_count, col + 10, _('Total Cost'), format_title)

                sheet.merge_range(rowy, col + 11, rowy, col + 13, _('DIFFERENCE'), format_title)
                sheet.write(rowy + f4_count, col + 11, _('Quantity'), format_title)
                sheet.write(rowy + f4_count, col + 12, _('Price Unit'), format_title)
                sheet.write(rowy + f4_count, col + 13, _('Total Cost'), format_title)

                f4_count += 1
                f3_count += 1
                start_row = rowx + 3
                rowxinner = rowx + 3
                in_dictionary = result_dict[result_dict[dict]['tr_id']]['in']
                if not in_dictionary:
                    out_dict_count = result_dict[result_dict[dict]['tr_id']]['out']
                    for obj in out_dict_count:
                        vls = {'picking_name': '', 'product_name': '', 'product_id': 0.0, 'qty': 0.0, 'price_unit': 0.0, 'sub_total': 0.0}
                        in_dictionary.append(vls)
                for in_dict in in_dictionary:
                    sheet.write(rowy + f3_count, col + 7, in_dict['picking_name'], format_content_text)
                    sheet.write(rowy + f3_count, col + 8, in_dict['qty'], format_content_text)
                    sheet.write(rowy + f3_count, col + 9, in_dict['price_unit'], format_content_left_float)

                    sum_in_qty += in_dict['qty']
                    sum_in_price_unit += in_dict['price_unit']
                    sum_in_sub_total += in_dict['sub_total']

                    sheet.write_formula('K%s' % rowxinner, '{=(I%s * J%s)}' % (rowxinner, rowxinner), format_content_left_float)
                    sheet.write_formula('L%s' % rowxinner, '{=(E%s - I%s)}' % (rowxinner, rowxinner), format_content_left_float)
                    sheet.write_formula('M%s' % rowxinner, '{=(F%s - J%s)}' % (rowxinner, rowxinner), format_content_left_float)
                    sheet.write_formula('N%s' % rowxinner, '{=(L%s * M%s)}' % (rowxinner, rowxinner), format_content_left_float)
                    f3_count += 1
                    f4_count += 1
                    in_count += 1
                    rowxinner += 1

                f4_count = 1
                f4_count += 1
                for q_dict in qty_dict:
                    if result_dict[dict]['tr_id'] in q_dict:
                        sum_qty_dict_qty += qty_dict[q_dict]['qty']
                count += 1
                rowx += max(f1_count, f2_count, f3_count, f4_count)
                last_row = rowxinner
                last_row -= 1

                if out_count != in_count:
                    if out_count > in_count:
                        rowxinner += out_count - in_count

                sheet.write(rowx, 0, u'', format_title)
                sheet.write(rowx, 1, _('Total amount'), format_title)
                sheet.write(rowx, 2, u'', format_title)
                sheet.write(rowx, 3, u'', format_title)
                sheet.write(rowx, 4, sum_out_qty, format_title)
                sheet.write(rowx, 5, sum_out_price_unit, format_title)
                sheet.write(rowx, 6, sum_out_sub_total, format_title)
                sheet.write(rowx, 7, u'', format_title)
                sheet.write(rowx, 8, sum_in_qty, format_title)
                sheet.write(rowx, 9, u'', format_title)
                sheet.write_formula('K%s' % rowxinner, '{=SUM(K%s:K%s)}' % (start_row, last_row), format_title)
                sheet.write(rowx, 11, sum_qty_dict_qty, format_title)
                sheet.write(rowx, 12, u'', format_title)
                sheet.write_formula('N%s' % rowxinner, '{=SUM(N%s:N%s)}' % (start_row, last_row), format_title)
                rowx += 2

        sheet.set_column(0, 0, 4)
        sheet.set_column(1, 1, 18)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 18)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 5, 18)
        sheet.set_column(6, 6, 18)
        sheet.set_column(7, 7, 18)
        sheet.set_column(8, 8, 18)
        sheet.set_column(9, 9, 18)
        sheet.set_column(10, 10, 18)
        sheet.set_column(11, 11, 18)
        sheet.set_column(12, 12, 18)
        sheet.set_column(13, 13, 18)

        book.close()

        # set file data
        report_excel_output_obj.filedata = base64.b64encode(output.getvalue())

        # call export function
        return report_excel_output_obj.export_report()