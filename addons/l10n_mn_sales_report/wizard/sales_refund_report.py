# -*- encoding: utf-8 -*-
import base64
from io import BytesIO
import time
import xlsxwriter

from odoo import api, fields, models, _
from odoo.addons.l10n_mn_report.models.report_helper import *
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles
from odoo.addons.l10n_mn_web.models.time_helper import *
from odoo.exceptions import UserError


class SalesRetrievalReport(models.TransientModel):
    """
        Борлуулалтын буцаалтын тайлан
    """

    _name = 'sales.refund.report'
    _description = "Sales Refund Report"

    GROUP_SELECTION = [
        ('no_group', 'No Group'),
        ('by_warehouse', 'Group by Warehouse'),
        ('by_partner', 'Group by Partner'),
        ('by_category', 'Group by Product Category')
    ]

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id)
    group_type = fields.Selection(GROUP_SELECTION, default='no_group', required=True)

    date_start = fields.Date("Start Date", required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date("End Date", required=True, default=lambda *a: time.strftime('%Y-%m-%d'))

    show_barcode = fields.Boolean(string='See Product Bar Code', default=False)
    group_by_sale_order = fields.Boolean(string='Group By Sale Order', default=False)

    warehouse_ids = fields.Many2many('stock.warehouse', 'sales_refund_report_to_warehouse', 'report_id', 'warehouse_id', string="Warehouses")
    category_ids = fields.Many2many('product.category', 'sales_refund_report_to_category', 'report_id', 'category_id', string="Category")
    product_ids = fields.Many2many('product.product', 'sales_refund_report_to_product_product', 'report_id', 'product_id', string="Products")
    partner_ids = fields.Many2many('res.partner', 'sales_refund_report_to_partner', 'report_id', 'so_id', string="Partners")

    @api.onchange("company_id")
    def _get_warehouse_and_categ_domain(self):
        domain = {}
        domain['warehouse_ids'] = [('company_id','=', self.company_id.id)]
        _warehouses = []
        for warehouse in self.env.user.allowed_warehouse_ids:
            _warehouses.append(warehouse.id)
        if _warehouses:
            domain['warehouse_ids'] = [('id', 'in', _warehouses), ('company_id','=', self.company_id.id)]
        domain['category_ids'] = [('company_id','=', self.company_id.id)]
        domain['product_ids'] = [('product_tmpl_id.company_id','=', self.company_id.id)]
        return {'domain': domain}

    @api.onchange("category_ids")
    def _get_product_domain(self):
        domain = {}
        if self.category_ids and len(self.category_ids) > 0:
            domain['product_ids'] = [('product_tmpl_id.categ_id','in', self.category_ids.ids)]
        return {'domain': domain}

    @api.onchange('group_type')
    def set_group_by_sale_order(self):
        for obj in self:
            if ((obj.group_type and obj.group_type == 'no_group') or not obj.group_type) and not obj.group_by_sale_order:
                obj.group_by_sale_order = True

    @api.onchange('date_start', 'date_end')
    def validate_date_range_start(self):
        if self.date_start and self.date_end:
            if self.date_start > self.date_end:
                raise UserError('Invalid date range, Please enter a date start less than or equal to date end')

    def get_all_col_count(self):
        all_col_count = 15
        all_col_count += 1 if self.show_barcode else 0
        return all_col_count

    def get_group_name(self):
        if self.group_type and self.group_type == 'by_warehouse':
            return _("Warehouse")
        elif self.group_type and self.group_type == 'by_category':
            return _("Product Category")
        elif self.group_type and self.group_type == 'by_partner':
            return _("Partner")
        return False

    def get_lines(self):

        date_from = get_display_day_to_user_day(str(self.date_start) + ' 00:00:00', self.env.user)
        date_to = get_display_day_to_user_day(str(self.date_end) + ' 23:59:59', self.env.user)

        order_by_qry = ""
        main_select = ""
        if self.group_type and self.group_type == 'by_warehouse':
            order_by_qry = ' wh.name, wh.id, '
            main_select = 'wh.id AS group_id, wh.name AS group_name, '
        elif self.group_type and self.group_type == 'by_category':
            order_by_qry = ' pro_cat.name, pro_cat.id, '
            main_select = 'pro_cat.id AS group_id, pro_cat.name AS group_name, '
        elif self.group_type and self.group_type == 'by_partner':
            order_by_qry = ' partner.name, partner.id, '
            main_select = 'partner.id AS group_id, partner.name AS group_name, '
        if self.group_by_sale_order:
            order_by_qry += ' so.name, so.id, so.date_order, '

        where_qry = ""
        if self.warehouse_ids:
            warehouse_ids = self.warehouse_ids.ids
            where_qry += ' AND wh.id in (' + ','.join(map(str, warehouse_ids)) + ') '
        if self.category_ids:
            category_ids = self.category_ids.ids
            where_qry += ' AND pro_cat.id in (' + ','.join(map(str, category_ids)) + ') '
        if self.product_ids:
            product_ids = self.product_ids.ids
            where_qry += ' AND pp.id in (' + ','.join(map(str, product_ids)) + ') '
        if self.partner_ids:
            so_ids = self.partner_ids.ids
            where_qry += ' AND partner.id in (' + ','.join(map(str, so_ids)) + ') '

        qry = """
            SELECT %s
                so.id AS so_id, so.name AS so_name, so.date_order, pp.id AS pro_id, pp.barcode AS barcode, pt.default_code AS default_code, pt.name AS pt_name, COALESCE(translation.value, uom.name) AS uom_name,
                all_sale_order.unit_price_after_discount AS so_unit_price,
                all_sale_order.sum_quantity AS so_total_quantity,
                refund_from_picking.unit_price AS refund_picking_unit_price,
                refund_from_picking.sum_quantity AS refund_picking_total_quantity,
                refund_from_invoice.unit_price_after_discount AS refund_invoice_unit_price,
                refund_from_invoice.sum_quantity AS refund_invoice_total_quantity
            FROM

            /* TABLE all_sale_order: Бүх борлуулалтын захиалга дахь барааны НИЙТ ТОО ХЭМЖЭЭ, НЭГЖ ҮНЭ -г олох. (БЗ > Бараа > Нэгжийн үнэ)-р бүлэглэх*/
            (
                SELECT so_id, pro_id, unit_price_after_discount, sum(quantity) AS sum_quantity
                FROM
                (
                    SELECT sol.order_id AS so_id, sol.product_id AS pro_id, sol.product_uom_qty AS quantity, (sol.price_unit*(1-(sol.discount)/100)) AS unit_price_after_discount
                     FROM sale_order_line sol
                ) table1
                GROUP BY so_id, pro_id, unit_price_after_discount
            ) all_sale_order


            LEFT JOIN
            /* TABLE refund_from_picking: БЗ-ын хүргэлтийн буцаалт дахь НИЙТ ТОО ХЭМЖЭЭ, НЭГЖ ҮНЭ -г олох. (БЗ > Бараа > Нэгжийн үнэ)-р бүлэглэх*/
            (
                SELECT so_id, pro_id, unit_price, abs(sum(quantity)) AS sum_quantity
                FROM
                (
                    SELECT sol.order_id  AS so_id, sm.product_id AS pro_id, sol.price_unit AS unit_price,
                    /*Хэрвээ буцаасан хүргэлтээс ахиад буцааж байгаа бол уг буцаалт нь анхны хүргэлтийн хувьд буцаалтынхаа хэмжээгээр хүчингүйд тооцогдох буюу буцаагаагүй гэж үзнэ*/
                    case when dest_loc.usage = 'internal' then COALESCE(-sm.product_uom_qty)
                        else sm.product_uom_qty end AS quantity
                     FROM sale_order_line sol
                    LEFT JOIN stock_move sm ON sm.sale_line_id = sol.id
                    LEFT JOIN stock_location dest_loc ON dest_loc.id = sm.location_dest_id
                    where sm.state = 'done' AND sm.origin_returned_move_id IS NOT NULL
                ) table1
                GROUP BY so_id, pro_id, unit_price
            ) refund_from_picking ON refund_from_picking.so_id = all_sale_order.so_id AND refund_from_picking.pro_id = all_sale_order.pro_id


            LEFT JOIN
            /* TABLE refund_from_invoice: БЗ-ын нэхэмжлэлийн төлбөрийн буцаалт дахь НИЙТ ТОО ХЭМЖЭЭ, НЭГЖ ҮНЭ -г олох. (БЗ > Бараа > Нэгжийн үнэ)-р бүлэглэх*/
            (
                SELECT so_id, pro_id, unit_price_after_discount, sum(quantity) AS sum_quantity
                FROM
                (
                    SELECT so.id AS so_id, refund_invoice_line.product_id AS pro_id, refund_invoice_line.quantity AS quantity,
                        (refund_invoice_line.price_unit*(1-(refund_invoice_line.discount)/100)) AS unit_price_after_discount
                    FROM account_move refund_inv
                    LEFT JOIN account_move_line refund_invoice_line ON refund_invoice_line.move_id = refund_inv.id
                    LEFT JOIN sale_order so ON so.name = refund_inv.invoice_origin
                    where refund_inv.state NOT IN ('draft', 'cancel') AND refund_inv.move_type = 'out_refund' AND refund_inv.invoice_origin in
                    (
                        SELECT out_inv.name
                         FROM account_move out_inv
                        right join sale_order so ON so.name = out_inv.invoice_origin
                        where out_inv.move_type = 'out_invoice' AND out_inv.invoice_origin IS NOT NULL
                    )
                ) table1
                GROUP BY so_id, pro_id, unit_price_after_discount
            ) refund_from_invoice ON refund_from_invoice.so_id = all_sale_order.so_id AND refund_from_invoice.pro_id = all_sale_order.pro_id

            LEFT JOIN sale_order so ON so.id = all_sale_order.so_id
            LEFT JOIN product_product pp ON pp.id = all_sale_order.pro_id
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN uom_uom uom ON uom.id = pt.uom_id
            LEFT JOIN ir_translation translation ON translation.src = uom.name AND translation.res_id = uom.id AND translation.lang = 'mn_MN' AND translation.name = 'product.uom,name'
            LEFT JOIN product_category pro_cat ON pt.categ_id = pro_cat.id
            LEFT JOIN stock_warehouse wh ON wh.id = so.warehouse_id
            LEFT JOIN res_partner partner ON partner.id = so.partner_id
            WHERE so.company_id = %s AND so.state IN ('done', 'sale') AND so.date_order BETWEEN '%s' AND '%s' AND (refund_from_picking.so_id IS NOT NULL OR refund_from_invoice.so_id IS NOT NULL) %s
            ORDER BY %s pp.barcode, pt.default_code, uom.name, all_sale_order.sum_quantity
        """ % (main_select, self.company_id.id, date_from, date_to, where_qry, order_by_qry)

        self._cr.execute(qry)
        results = self._cr.dictfetchall()
        return results if results else False

    def export_report(self):
        # create workbook
        output = BytesIO()
        book = xlsxwriter.Workbook(output)

        # create name
        report_name = _('Sales Refund Report')
        file_name = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'),)

        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=('moving_materials_report'), form_title=file_name).create({})

        # register formats
        format_filter = book.add_format(ReportExcelCellStyles.format_filter)
        format_filter_right = book.add_format(ReportExcelCellStyles.format_filter_right)
        format_name = book.add_format(ReportExcelCellStyles.format_name)
        format_title = book.add_format(ReportExcelCellStyles.format_title)
        format_title_float = book.add_format(ReportExcelCellStyles.format_title_float)
        format_content_text = book.add_format(ReportExcelCellStyles.format_content_text)
        format_content_float_color = book.add_format(ReportExcelCellStyles.format_content_float_color)
        format_content_center = book.add_format(ReportExcelCellStyles.format_content_center)
        format_content_float = book.add_format(ReportExcelCellStyles.format_content_float)
        format_group_number = book.add_format(ReportExcelCellStyles.format_group_number)
        format_group_left = book.add_format(ReportExcelCellStyles.format_group_left)

        # create sheet
        sheet = book.add_worksheet(report_name)
        sheet.set_landscape()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.78, 0.39, 0.39, 0.39)  # 2cm, 1cm, 1cm, 1cm
        sheet.set_footer('&C&"Times New Roman"&9&P', {'margin': 0.1})
        rowx = 0

        # compute column
        col = 0
        sheet.set_column(get_xsl_column_name(col), 4)
        if self.show_barcode:
            col += 1
            sheet.set_column(get_xsl_column_name(col), 10)
        sheet.set_column(get_xsl_column_name(col+1), 10)
        sheet.set_column(get_xsl_column_name(col+2), 10)
        sheet.set_column(get_xsl_column_name(col+3), 30)
        sheet.set_column(get_xsl_column_name(col+4), 8)
        for i in range(col+5, self.get_all_col_count(), 3):
            sheet.set_column(get_xsl_column_name(i), 10)
            sheet.set_column(get_xsl_column_name(i+1), 15)
            sheet.set_column(get_xsl_column_name(i+2), 15)

        # create contents
        sheet.merge_range(rowx, 0, rowx, self.get_all_col_count(), _(u'Company') + u": %s" % str(self.company_id.name), format_filter)
        sheet.merge_range(rowx+2, 0, rowx+3, self.get_all_col_count(), report_name, format_name)
        sheet.merge_range(rowx+5, 0, rowx+5, 3, _(u'Report Date') + u": %s ~ %s" % (str(self.date_start), str(self.date_end)), format_filter)
        start_col = 13 if self.show_barcode else 12
        sheet.merge_range(rowx+5, start_col, rowx+5, start_col+1, _(u'Printed Date') + u": %s" % get_day_like_display(fields.Datetime.now(), self.env.user), format_filter_right)

        rowx += 6
        col = 0
        sheet.merge_range(rowx, col, rowx+1, col, u'№', format_title)
        if self.show_barcode:
            col += 1
            sheet.merge_range(rowx, col, rowx+1, col, _(u'Product Bar Code'), format_title)
        sheet.merge_range(rowx, col+1, rowx+1, col+1, _(u'Origin Number'), format_title)
        sheet.merge_range(rowx, col+2, rowx+1, col+2, _(u'Internal Reference'), format_title)
        sheet.merge_range(rowx, col+3, rowx+1, col+3, _(u'Product'), format_title)
        col += 1
        sheet.merge_range(rowx, col+3, rowx+1, col+3, _(u'Unit of measure'), format_title)
        sheet.merge_range(rowx, col+4, rowx, col+6, _(u'Sale'), format_title)
        sheet.write(rowx+1, col+4, _(u'Quantity'), format_title)
        sheet.write(rowx+1, col+5, _(u'Unit Price'), format_title)
        sheet.write(rowx+1, col+6, _(u'Total Price'), format_title)
        col += 3
        sheet.merge_range(rowx, col+4, rowx, col+6, _(u'Picking Refund'), format_title)
        sheet.write(rowx+1, col+4, _(u'Quantity'), format_title)
        sheet.write(rowx+1, col+5, _(u'Unit Price'), format_title)
        sheet.write(rowx+1, col+6, _(u'Total Price'), format_title)
        col += 3
        sheet.merge_range(rowx, col+4, rowx, col+6, _(u'Invoice Refund'), format_title)
        sheet.write(rowx+1, col+4, _(u'Quantity'), format_title)
        sheet.write(rowx+1, col+5, _(u'Unit Price'), format_title)
        sheet.write(rowx+1, col+6, _(u'Total Price'), format_title)

        results = self.get_lines()
        rowx += 2

        writen_group_ids, writen_so_ids = [], []
        group_rows, so_rows, pp_rows = [], [], []
        current_group_rowx, current_so_rowx = -1, -1

        all_pp_line_count = 0

        all_col_count = self.get_all_col_count()
        main_col_count = 5 + (1 if self.show_barcode else 0)

        startx, endx = -1, -1

        if results:
            startx, endx = rowx + 1, rowx + 1
            for result in results:
                if self.group_type and self.group_type != 'no_group' and result['group_id'] not in writen_group_ids:
                    writen_group_ids.append(result['group_id'])
                    group_rows.append(rowx+1)

                    sheet.merge_range(rowx, 0, rowx, main_col_count - 1, "%s: %s" %(self.get_group_name(), result['group_name']), format_group_left)

                    if current_group_rowx != -1:
                        if self.group_by_sale_order and so_rows:
                            for i in range(main_col_count, all_col_count - 1, 3):
                                sheet.write_formula(current_group_rowx, i, get_sum_formula_from_list(i, so_rows), format_content_float_color)
                                sheet.write(current_group_rowx, i+1, "", format_content_float_color)
                                sheet.write_formula(current_group_rowx, i+2, get_sum_formula_from_list(i+2, so_rows), format_content_float_color)
                        else:
                            if pp_rows:
                                for i in range(main_col_count, all_col_count - 1, 3):
                                    sheet.write_formula(current_group_rowx, i, get_sum_formula(pp_rows[0], pp_rows[-1], i), format_content_float_color)
                                    sheet.write(current_group_rowx, i+1, "", format_content_float_color)
                                    sheet.write_formula(current_group_rowx, i+2, get_sum_formula(pp_rows[0], pp_rows[-1], i+2), format_content_float_color)
                    if self.group_by_sale_order and current_so_rowx != -1:
                        if pp_rows:
                            for i in range(main_col_count, all_col_count - 1, 3):
                                sheet.write_formula(current_so_rowx, i, get_sum_formula(pp_rows[0], pp_rows[-1], i), format_title_float)
                                sheet.write(current_so_rowx, i+1, "", format_title_float)
                                sheet.write_formula(current_so_rowx, i+2, get_sum_formula(pp_rows[0], pp_rows[-1], i+2), format_title_float)

                    so_rows = []
                    pp_rows = []
                    writen_so_ids = []
                    current_group_rowx = rowx
                    rowx += 1

                if self.group_by_sale_order and result['so_id'] not in writen_so_ids:
                    writen_so_ids.append(result['so_id'])
                    so_rows.append(rowx+1)

                    sheet.merge_range(rowx, 0, rowx, main_col_count - 1, "%s: %s" %(result['so_name'], result['date_order']), format_group_number)

                    if current_so_rowx != -1:
                        if pp_rows:
                            for i in range(main_col_count, all_col_count - 1, 3):
                                sheet.write_formula(current_so_rowx, i, get_sum_formula(pp_rows[0], pp_rows[-1], i), format_title_float)
                                sheet.write(current_so_rowx, i+1, "", format_title_float)
                                sheet.write_formula(current_so_rowx, i+2, get_sum_formula(pp_rows[0], pp_rows[-1], i+2), format_title_float)

                    pp_rows = []
                    current_so_rowx = rowx
                    rowx += 1

                all_pp_line_count += 1
                pp_rows.append(rowx+1)
                col = 0
                sheet.write(rowx, col, all_pp_line_count, format_content_center)
                if self.show_barcode:
                    col += 1
                    sheet.write(rowx, col, result.get("barcode") or "", format_content_center)
                sheet.write(rowx, col+1, result.get("so_name") or "", format_content_center)
                sheet.write(rowx, col+2, result.get("default_code") or 0, format_content_center)
                sheet.write(rowx, col+3, result.get("pt_name") or 0, format_content_text)
                sheet.write(rowx, col+4, result.get("uom_name") or 0, format_content_center)
                sheet.write(rowx, col+5, result.get("so_total_quantity") or 0, format_content_float)
                sheet.write(rowx, col+6, result.get("so_unit_price") or 0, format_content_float)
                sheet.write_formula(rowx, col+7, get_arithmetic_formula(col+5, rowx, col+6, rowx, '*'), format_content_float)
                col += 3
                sheet.write(rowx, col+5, result.get("refund_picking_total_quantity") or 0, format_content_float)
                sheet.write(rowx, col+6, result.get("refund_picking_unit_price") or 0, format_content_float)
                sheet.write_formula(rowx, col+7, get_arithmetic_formula(col+5, rowx, col+6, rowx, '*'), format_content_float)
                col += 3
                sheet.write(rowx, col+5, result.get("refund_invoice_total_quantity") or 0, format_content_float)
                sheet.write(rowx, col+6, result.get("refund_invoice_unit_price") or 0, format_content_float)
                sheet.write_formula(rowx, col+7, get_arithmetic_formula(col+5, rowx, col+6, rowx, '*'), format_content_float)

                endx = rowx
                rowx += 1

                if results[-1] == result:
                    if current_group_rowx != -1:
                        if self.group_by_sale_order and so_rows:
                            for i in range(main_col_count, all_col_count - 1, 3):
                                sheet.write_formula(current_group_rowx, i, get_sum_formula_from_list(i, so_rows), format_content_float_color)
                                sheet.write(current_group_rowx, i+1, "", format_content_float_color)
                                sheet.write_formula(current_group_rowx, i+2, get_sum_formula_from_list(i+2, so_rows), format_content_float_color)
                        else:
                            if pp_rows:
                                for i in range(main_col_count, all_col_count - 1, 3):
                                    sheet.write_formula(current_group_rowx, i, get_sum_formula(pp_rows[0], pp_rows[-1], i), format_content_float_color)
                                    sheet.write(current_group_rowx, i+1, "", format_content_float_color)
                                    sheet.write_formula(current_group_rowx, i+2, get_sum_formula(pp_rows[0], pp_rows[-1], i+2), format_content_float_color)
                    if self.group_by_sale_order and current_so_rowx != -1:
                        if pp_rows:
                            for i in range(main_col_count, all_col_count - 1, 3):
                                sheet.write_formula(current_so_rowx, i, get_sum_formula(pp_rows[0], pp_rows[-1], i), format_title_float)
                                sheet.write(current_so_rowx, i+1, "", format_title_float)
                                sheet.write_formula(current_so_rowx, i+2, get_sum_formula(pp_rows[0], pp_rows[-1], i+2), format_title_float)

            # build content footer
            sheet.merge_range(rowx, 0, rowx, main_col_count - 1, _("TOTAL"), format_title)
            for i in range(main_col_count, all_col_count - 1, 3):
                if self.group_type and self.group_type != 'no_group':
                    sheet.write_formula(rowx, i, get_sum_formula_from_list(i, group_rows), format_content_float_color)
                    sheet.write_formula(rowx, i+2, get_sum_formula_from_list(i+2, group_rows), format_content_float_color)
                elif self.group_by_sale_order:
                    sheet.write_formula(rowx, i, get_sum_formula_from_list(i, so_rows), format_content_float_color)
                    sheet.write_formula(rowx, i+2, get_sum_formula_from_list(i+2, so_rows), format_content_float_color)
                elif (startx != -1 and endx != -1):
                    sheet.write_formula(rowx, i, get_sum_formula(startx, endx, i), format_content_float_color)
                    sheet.write_formula(rowx, i+2, get_sum_formula(startx, endx, i+2), format_content_float_color)
                sheet.write(rowx, i+1, "", format_content_float_color)

            rowx += 3
            sheet.merge_range(rowx, 1, rowx, 3, _(u"Checked By") + u": ............................................ ............... /                                                /", format_filter)

        book.close()
        # set file data
        report_excel_output_obj.filedata = base64.encodebytes(output.getvalue())
        # call export function
        return report_excel_output_obj.export_report()