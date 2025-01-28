# -*- encoding: utf-8 -*-
##############################################################################
import base64
import time
import xlsxwriter
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.l10n_mn_web.models.time_helper import *
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles


class ReportSalesReport(models.TransientModel):
    """
        Борлуулалтын дэлгэрэнгүй тайлан
    """

    _name = 'report.sales'
    _description = "Sales Report"

    def _default_warehouse(self):
        _warehouse_ids = []
        for warehouse in self.env.user.allowed_warehouse_ids:
            _warehouse_ids.append(warehouse.id)
        if _warehouse_ids:
            return [('id', 'in', _warehouse_ids)]
        else:
            return []

    # Ижил шатлал сонгосон эсэхийг шалгах
    @api.onchange('stage_two', 'stage_three')
    def _no_same_stage(self):
        if (self.stage_one == self.stage_two or self.stage_one == self.stage_three or self.stage_two == self.stage_three) and self.group == True:
            raise UserError(_("You must choose three different stages!"))

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env['res.company']._company_default_get('report.sales'))
    group = fields.Boolean('Group', defualt=False)
    report_type = fields.Selection([('sales order', 'Sales Order'),
                                    ('invoice', 'Invoice'),
                                    ('shipment', 'Shipment'),
                                    ('done', 'Done'),
                                     ('loan', 'loan')], string='Report Type', help='Choose type of sales report.\
                                        The report based on only sale order\'Sale Order\'.\
                                        The report based on invoice of sale orders. \'Invoice\' .\
                                        The report based on picking of sale orders. \'Shipment\'.\
                                        The report based on invoice, picking, sale order. \'Done\' ', default='shipment', required=True)
    # date_from = fields.Date("Start Date", required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_from = fields.Date("Start Date", required=True, default=lambda *a: time.strftime('%Y-01-01'))
    date_to = fields.Date("End Date", required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    see_profit = fields.Boolean(string='See Profit', default=False) # Зөвхөн өртөг харах дүртэй хүн болон тайлан тээвэрлэлтээр эсвэл дууссан төлөвөөр татах үед харагдана.
    see_serial = fields.Boolean(string='See Serial', default=False) # Зөвхөн өртөг харах дүртэй хүнд харагдана.
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouses", domain=_default_warehouse)
    category_ids = fields.Many2many('product.category', string="Category")
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string="Products")
    lot_ids = fields.Many2many('stock.production.lot', string="Lot")
    partner_ids = fields.Many2many('res.partner', 'sales_report_partner_report_rel','partner_id','report_id',string="Partner", domain=[('is_customer', '=', True)])
    salesperson_ids = fields.Many2many('res.users', string="Salesperson")
    brand_ids = fields.Many2many('product.brand', string="Brands")
    salesteam_ids = fields.Many2many('crm.team', string="Sales Teams")
    supplier_ids = fields.Many2many('res.partner','sales_report_supplier_report_rel','supplier_id','report_id', string="Suppliers", domain=[('is_supplier', '=', True)])
    invis_location = fields.Boolean('invinsible', default=False) # location - талбарын харагдах/харагдахгүй утга хадгалах хувьсагч
    invis_profit = fields.Boolean('invinsible', default=False) # profit - талбарын харагдах/харагдахгүй утга хадгалах хувьсагч
    stage_one = fields.Selection([('warehouse', 'Warehouse'),
                                  ('location', 'Location'),
                                  ('categ', 'Product Category'),
                                  ('brand', 'Product Brand'),
                                  ('salesman', 'Salesman'),
                                  ('salesteam', 'Salesteam'),
                                  ('customer', 'Customer'),
                                  ('supplier', 'Supplier')], string='Stage 1')
    stage_two = fields.Selection([('warehouse', 'Warehouse'),
                                  ('location', 'Location'),
                                  ('categ', 'Product Category'),
                                  ('brand', 'Product Brand'),
                                  ('salesman', 'Salesman'),
                                  ('salesteam', 'Salesteam'),
                                  ('customer', 'Customer'),
                                  ('supplier', 'Supplier')], string='Stage 2')
    stage_three = fields.Selection([('warehouse', 'Warehouse'),
                                    ('location', 'Location'),
                                    ('categ', 'Product Category'),
                                    ('brand', 'Product Brand'),
                                    ('salesman', 'Salesman'),
                                    ('salesteam', 'Salesteam'),
                                    ('customer', 'Customer'),
                                    ('supplier', 'Supplier')], string='Stage 3')

    def get_column(self, sheet):
        # compute column
        if not self.company_id.account_sale_tax_id:
            colx_number = 10
        else:
            colx_number = 18
        sheet.set_column('A:A', 4)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 35)
        sheet.set_column('D:Z', 12)
        sheet.set_row(7, 30)
        sheet.set_row(8, 30)
        return sheet, colx_number

    def get_sheet(self, book, format, report_name):
        # create sheet
        sheet = book.add_worksheet(report_name)
        sheet.set_portrait()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.78, 0.39, 0.39, 0.39)  # 2cm, 1cm, 1cm, 1cm
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&C&"Times New Roman"&9&P', {'margin': 0.1})
        rowx = 1
        sheet, colx_number = self.get_column(sheet)
        #report type
        if self.report_type == 'sales order':
            report_type = _('Sale Order')
        elif self.report_type == 'invoice':
            report_type = _('Invoice')
        elif self.report_type == 'shipment':
            report_type = _('Shipment')
        elif self.report_type == 'done':
            report_type = _('Done')
        elif self.report_type == 'loan':
            report_type = _('Loan')
        # create company
        sheet.merge_range(rowx, 0, rowx, 2, '%s: %s' % (_('Company'), self.company_id and self.company_id.name or ''), format['format_filter'])
        rowx += 1
        sheet.merge_range(rowx, 0, rowx + 1, colx_number, report_name.upper(), format['format_name'])
        rowx += 2
        # create duration
        sheet.merge_range(rowx, 0, rowx, 3, '%s: %s - %s' % (_('Duration'), self.date_from, self.date_to), format['format_filter'])
        rowx += 1
        sheet.write(rowx, 0, _('Report type: %s') % (report_type), format['format_filter'])
        rowx += 1
        # create date
        sheet.merge_range(rowx, 0, rowx, 2, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format['format_filter'])
        rowx += 2
        return sheet, rowx

    def get_format(self, book):
        # create format
        return { 'format_name' : book.add_format(ReportExcelCellStyles.format_name),
                'format_filter' : book.add_format(ReportExcelCellStyles.format_filter),
                'format_filter_center' : book.add_format(ReportExcelCellStyles.format_filter_center),
                'format_title' : book.add_format(ReportExcelCellStyles.format_title),
                'format_title_small' : book.add_format(ReportExcelCellStyles.format_title_small),
                'format_title_float' : book.add_format(ReportExcelCellStyles.format_title_float),
                'format_content_center' : book.add_format(ReportExcelCellStyles.format_content_center),
                'format_content_text' : book.add_format(ReportExcelCellStyles.format_content_text),
                'format_content_text_color' : book.add_format(ReportExcelCellStyles.format_group_number),
                'format_content_float' : book.add_format(ReportExcelCellStyles.format_content_float),
                'format_content_left' : book.add_format(ReportExcelCellStyles.format_content_left),
                'format_red_text' : book.add_format(ReportExcelCellStyles.format_content_float_redcolor),
                'format_sub_text_float' : book.add_format(ReportExcelCellStyles.format_group_float),
                 }

    def get_title(self, sheet, rowx, col, report_name, format_name):
        #Тайлангийн гарчиг зурах
        if self.see_profit:
            col +=5
        if self.see_serial:
            col +=1
        sheet.merge_range(rowx, 0, rowx+1, col, report_name.upper(), format_name)
        return sheet

    def get_footer(self, sheet, rowx, format):
        #Тайлангийн гарын үсгийн хөл зурах
        sheet, col = self.get_column(sheet)
        if self.see_profit:
            col +=5
        if self.see_serial:
            col +=1
        sheet.merge_range(rowx, 0, rowx, col, '%s: ........................................... (                          )' % _('Made by'), format['format_filter'])
        rowx += 2
        sheet.merge_range(rowx, 0, rowx, col, '%s: ........................................... (                          )' % _('Check by'), format['format_filter'])
        return sheet

    def get_header(self, sheet, rowx, format_title, format_title_small, lot, sale_tax_pay, key, colx_to_start=0):
        #Тайлангийн толгой зурах
        if key:
            colx = 0
            sheet.merge_range(rowx, colx, rowx + 1, colx, _('№'), format_title)
            colx += 1
            sheet.merge_range(rowx, colx, rowx + 1, colx, _('Product code'), format_title)
            colx += 1
            sheet.merge_range(rowx, colx, rowx + 1, colx, _('Product name'), format_title)
            colx += 1
            sheet.merge_range(rowx, colx, rowx + 1, colx, _('Unit of measure'), format_title)
            colx += 1
            if lot != 0:  # Цувралтай бол цувралын нэрийг нэмнэ
                sheet.merge_range(rowx, colx, rowx + 1, colx, _('Lot Name'), format_title)
                colx += 1
        if colx_to_start:
            colx = colx_to_start
        else:
            colx = 5 if self.see_serial else 4
        sales_colx = colx
        plus = 1 if sale_tax_pay else 3
        sheet.merge_range(rowx, colx, rowx, colx + plus, _('Sales'), format_title)
        colx += 2 if sale_tax_pay else 4
        if sale_tax_pay:
            sheet.write(rowx, colx, _('Discount'), format_title)
            colx += 1
        else:
            sheet.merge_range(rowx, colx, rowx, colx + 2, _('Discount'), format_title)
            colx += 2 if sale_tax_pay else 3
        sheet.merge_range(rowx, colx, rowx, colx + plus, _('Reverse'), format_title)
        colx += 2 if sale_tax_pay else 4
        sheet.merge_range(rowx, colx, rowx, colx + plus, _('Net Sales'), format_title)
        colx += 2 if sale_tax_pay else 4
        if self.see_profit:
            sheet.merge_range(rowx, colx, rowx, colx + 4, _('Profit without Tax'), format_title)
        colx += 1
        sheet.write(rowx + 1, sales_colx, _('Quantity'), format_title)
        sales_colx += 1
        if not sale_tax_pay:
            sheet.write(rowx + 1, sales_colx, _('Cost without Tax'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Tax'), format_title)
            sales_colx += 1
        sheet.write(rowx + 1, sales_colx, _('Cost with Tax'), format_title)
        sales_colx += 1
        if not sale_tax_pay:
            sheet.write(rowx + 1, sales_colx, _('Discount without Tax'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Tax'), format_title)
            sales_colx += 1
        sheet.write(rowx + 1, sales_colx, _('Discount with Tax'), format_title)
        sales_colx += 1
        sheet.write(rowx + 1, sales_colx, _('Quantity'), format_title)
        sales_colx += 1
        if not sale_tax_pay:
            sheet.write(rowx + 1, sales_colx, _('Cost without Tax'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Tax'), format_title)
            sales_colx += 1
        sheet.write(rowx + 1, sales_colx, _('Cost with Tax'), format_title)
        sales_colx += 1
        sheet.write(rowx + 1, sales_colx, _('Quantity'), format_title)
        sales_colx += 1
        if not sale_tax_pay:
            sheet.write(rowx + 1, sales_colx, _('Cost without Tax'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Tax'), format_title)
            sales_colx += 1
        sheet.write(rowx + 1, sales_colx, _('Cost with Tax'), format_title)
        sales_colx += 1
        if self.see_profit:
            sheet.write(rowx + 1, sales_colx, _('Total Purchase Cost'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Purchase Cost'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Net Profit'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Profit for unit'), format_title)
            sales_colx += 1
            sheet.write(rowx + 1, sales_colx, _('Percent'), format_title)
        return sheet

    # Тайлангийн дэд гарчиг зурах
    def get_sub_header(self, sheet, rowx, category, serial_number, qty, sub_total, tax, total, without_tax_discount, tax_discount, with_tax_discount, rev_qty, rev_sub_total, rev_tax, rev_total, net_qty, net_sub_total, net_tax, net_total, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent, format_title, format_sub_text_float, key, sale_tax_pay, colx_to_start=0):
        if key:
            colx = 0
            sheet.write(rowx, colx, '', format_title)
            colx += 1
            sheet.merge_range(rowx, colx, rowx, colx + 2, category, format_title)
            colx += 3
            if self.see_serial:
                sheet.write(rowx, colx, '', format_title)
                colx += 1
        elif colx_to_start:
            colx = colx_to_start
        else:
            colx = 5 if self.see_serial else 4
        sheet.write(rowx, colx, qty, format_sub_text_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, sub_total, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, tax, format_sub_text_float)
            colx += 1
        sheet.write(rowx, colx, total, format_sub_text_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, without_tax_discount, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, tax_discount, format_sub_text_float)
            colx += 1
        sheet.write(rowx, colx, with_tax_discount, format_sub_text_float)
        colx += 1
        sheet.write(rowx, colx, rev_qty, format_sub_text_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, rev_sub_total, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, rev_tax, format_sub_text_float)
            colx += 1
        sheet.write(rowx, colx, rev_total, format_sub_text_float)
        colx += 1
        sheet.write(rowx, colx, net_qty, format_sub_text_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, net_sub_total, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, net_tax, format_sub_text_float)
            colx += 1
        sheet.write(rowx, colx, net_total, format_sub_text_float)
        if self.see_profit:
            colx += 1
            sheet.write(rowx, colx, net_cost_price, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, cost_price_unit, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, net_profit, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, profit_of_unit, format_sub_text_float)
            colx += 1
            sheet.write(rowx, colx, percent, format_sub_text_float)
        return sheet

    # Тайлангийн хөлийн нийлбэр дүнгүүд зурах
    def _get_footer_total_amount(self, sheet, rowx, format_title, format_title_float, total_qty, total_price, total_tax, total_price_tax, total_without_tax_discount, total_tax_discount, total_with_tax_discount, total_rev_qty, total_rev_price, total_rev_tax,\
                                total_rev_price_tax, net_total_qty, total_price_net, total_tax_net, total_price_tax_net, total_purchase_cost_row, total_standard_cost,lot,sale_tax_pay, key, colx_to_start = 0):
        if key:
            colx = 0
            sheet.write(rowx, 0, '', format_title)
            colx+=1
            sheet.merge_range(rowx, colx, rowx, colx + 1, _('TOTAL'), format_title)
            colx+=2
            sheet.write(rowx, colx, '', format_title)
            colx += 1
            if lot:
                sheet.write(rowx, colx, '', format_title)
                colx += 1
        if colx_to_start:
            colx = colx_to_start
        else:
            colx = 5 if self.see_serial else 4
        sheet.write(rowx, colx, total_qty, format_title_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, total_price, format_title_float)
            colx += 1
            sheet.write(rowx, colx, total_tax, format_title_float)
            colx += 1
        sheet.write(rowx, colx, total_price_tax, format_title_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, total_without_tax_discount, format_title_float)
            colx += 1
            sheet.write(rowx, colx, total_tax_discount, format_title_float)
            colx += 1
        sheet.write(rowx, colx, total_with_tax_discount, format_title_float)
        colx += 1
        sheet.write(rowx, colx, total_rev_qty, format_title_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, total_rev_price, format_title_float)
            colx += 1
            sheet.write(rowx, colx, total_rev_tax, format_title_float)
            colx += 1
        sheet.write(rowx, colx, total_rev_price_tax, format_title_float)
        colx += 1
        sheet.write(rowx, colx, net_total_qty, format_title_float)
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, total_price_net, format_title_float)
            colx += 1
            sheet.write(rowx, colx, total_tax_net, format_title_float)
            colx += 1
        sheet.write(rowx, colx, total_price_tax_net, format_title_float)
        colx += 1
        if self.see_profit:
            sheet.write(rowx, colx, total_purchase_cost_row, format_title_float)
            colx += 1
            sheet.write(rowx, colx, total_standard_cost, format_title_float)
            colx += 1
            sheet.write(rowx, colx, total_price_net - total_purchase_cost_row, format_title_float)
            colx += 1
            sheet.write(rowx, colx, ((total_price_net - total_purchase_cost_row)/net_total_qty) if net_total_qty !=0 else 0, format_title_float)
            colx += 1
            sheet.write(rowx, colx, ((total_price_net - total_purchase_cost_row)*100/total_purchase_cost_row) if total_purchase_cost_row !=0 else 0, format_title_float)
            colx += 1
        return sheet

    #Дэд гарчгуудын дүнг 0лэх
    def _fill_zero(self, dict):
        dict['qty'] = 0
        dict['sub_total'] = 0
        dict['tax'] = 0
        dict['total'] = 0
        dict['without_tax_discount'] = 0
        dict['tax_discount'] = 0
        dict['with_tax_discount'] = 0
        dict['rev_qty'] = 0
        dict['rev_sub_total'] = 0
        dict['rev_tax'] = 0
        dict['rev_total'] = 0
        dict['net_qty'] = 0
        dict['net_sub_total'] = 0
        dict['net_tax'] = 0
        dict['net_total'] = 0
        dict['net_cost_price'] = 0
        dict['unit_price'] = 0
        dict['net_profit'] = 0
        dict['profit_of_unit'] = 0
        dict['percent'] = 0
        return dict

    #Дэд гарчгуудын нийлбэр дүнг олох
    def _fill_sum_value(self, dict, qty, sub_total, tax, total, without_tax_discount, tax_discount, with_tax_discount, rev_qty, rev_sub_total, rev_tax, rev_total, net_qty, net_sub_total, net_tax, net_total, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent):
        dict['qty'] += qty
        dict['sub_total'] += sub_total
        dict['tax'] += tax
        dict['total'] += total
        dict['without_tax_discount'] += without_tax_discount
        dict['tax_discount'] += tax_discount
        dict['with_tax_discount'] += with_tax_discount
        dict['rev_qty'] += rev_qty
        dict['rev_sub_total'] += rev_sub_total
        dict['rev_tax'] += rev_tax
        dict['rev_total'] += rev_total
        dict['net_qty'] += net_qty
        dict['net_sub_total'] += net_sub_total
        dict['net_tax'] += net_tax
        dict['net_total'] += net_total
        dict['net_cost_price'] += net_cost_price
        dict['unit_price'] += cost_price_unit
        dict['net_profit'] += net_profit
        dict['profit_of_unit'] += profit_of_unit
        dict['percent'] += percent
        return dict

    #Тайлангийн бүлэглэлтийн шатыг шалгах
    def _stage_check(self, state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum):
        if state == 'stage_one':
            del check_warehouse_ids[:]
            del check_location_ids[:]
            del check_cat_ids[:]
            del check_brand_ids[:]
            del check_salesman_ids[:]
            del check_salesteam_ids[:]
            del check_customer_ids[:]
            del check_supplier_ids[:]
            warehouse_sum = self._fill_zero(warehouse_sum)
            location_sum = self._fill_zero(location_sum)
            cat_sum = self._fill_zero(cat_sum)
            brand_sum = self._fill_zero(brand_sum)
            salesman_sum = self._fill_zero(salesman_sum)
            salesteam_sum = self._fill_zero(salesteam_sum)
            customer_sum = self._fill_zero(customer_sum)
            supplier_sum = self._fill_zero(supplier_sum)
        elif state == 'stage_two':
            check_warehouse_ids = [] if self.stage_one != 'warehouse' else check_warehouse_ids
            check_location_ids = [] if self.stage_one != 'location' else check_location_ids
            check_cat_ids = [] if self.stage_one != 'categ' else check_cat_ids
            check_brand_ids = [] if self.stage_one != 'brand' else check_brand_ids
            check_salesman_ids = [] if self.stage_one != 'salesman' else check_salesman_ids
            check_salesteam_ids = [] if self.stage_one != 'salesteam' else check_salesteam_ids
            check_customer_ids = [] if self.stage_one != 'customer' else check_customer_ids
            check_supplier_ids = [] if self.stage_one != 'supplier' else check_supplier_ids
            warehouse_sum = self._fill_zero(warehouse_sum) if self.stage_one != 'warehouse' else warehouse_sum
            location_sum = self._fill_zero(location_sum) if self.stage_one != 'location' else location_sum
            cat_sum = self._fill_zero(cat_sum) if self.stage_one != 'categ' else cat_sum
            brand_sum = self._fill_zero(brand_sum) if self.stage_one != 'brand' else brand_sum
            salesman_sum = self._fill_zero(salesman_sum) if self.stage_one != 'salesman' else salesman_sum
            salesteam_sum = self._fill_zero(salesteam_sum) if self.stage_one != 'salesteam' else salesteam_sum
            customer_sum = self._fill_zero(customer_sum) if self.stage_one != 'customer' else customer_sum
        else:
            check_warehouse_ids = [] if self.stage_one != 'warehouse' or self.stage_two != 'warehouse' else check_warehouse_ids
            check_location_ids = [] if self.stage_one != 'location' or self.stage_two != 'location' else check_location_ids
            check_cat_ids = [] if self.stage_one != 'categ' or self.stage_two != 'categ' else check_cat_ids
            check_brand_ids = [] if self.stage_one != 'brand' or self.stage_two != 'brand' else check_brand_ids
            check_salesman_ids = [] if self.stage_one != 'salesman' or self.stage_two != 'salesman' else check_salesman_ids
            check_salesteam_ids = [] if self.stage_one != 'salesteam' else check_salesteam_ids
            check_customer_ids = [] if self.stage_one != 'customer' else check_customer_ids
            check_supplier_ids = [] if self.stage_one != 'supplier' else check_supplier_ids
            warehouse_sum = self._fill_zero(warehouse_sum) if self.stage_one != 'warehouse' and self.stage_two != 'warehouse' else warehouse_sum
            location_sum = self._fill_zero(location_sum) if self.stage_one != 'location' and self.stage_two != 'location' else location_sum
            cat_sum = self._fill_zero(cat_sum) if self.stage_one != 'categ' and self.stage_two != 'categ' else cat_sum
            brand_sum = self._fill_zero(brand_sum) if self.stage_one != 'brand' and self.stage_two != 'brand' else brand_sum
            salesman_sum = self._fill_zero(salesman_sum) if self.stage_one != 'salesman' and self.stage_two != 'salesman' else salesman_sum
            salesteam_sum = self._fill_zero(salesteam_sum) if self.stage_one != 'salesteam' and self.stage_two != 'salesteam' else salesteam_sum
            customer_sum = self._fill_zero(customer_sum) if self.stage_one != 'customer' and self.stage_two != 'customer' else customer_sum
            supplier_sum = self._fill_zero(supplier_sum) if self.stage_one != 'supplier' and self.stage_two != 'supplier' else supplier_sum
        return check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum

    """Бүлэглэлтийг тооцож зурна"""
    def stage_check(self, state, stage_name, record,
                    check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum,
                    sheet, lot, format_content_text_color, format_sub_text_float,
                    last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx,
                    rowx, sub_cat, sale_tax_pay):
        if stage_name == 'warehouse':
            if 'warehouse_id' in record and record['warehouse_id'] not in check_warehouse_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                name = self.env['stock.warehouse'].search([('id', '=', record['warehouse_id'])]).name
                self.get_sub_header(sheet, rowx, _('Warehouse ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_ware_rowx = rowx
                rowx += 1
                sub_cat += 1
        if stage_name == 'location':
            if not self.invis_location:
                if record['location_id'] not in check_location_ids:
                    check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                    name = self.env['stock.location'].search([('id', '=', record['location_id'])]).name
                    self.get_sub_header(sheet, rowx, _('Location ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                    last_location_rowx = rowx
                    rowx += 1
                    sub_cat += 1
        if stage_name == 'categ':
            if record['cat_id'] not in check_cat_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                name = self.env['product.category'].search([('id', '=', record['cat_id'])]).name or _(' Not Defined')
                self.get_sub_header(sheet, rowx, _('Category ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_cat_rowx = rowx
                rowx += 1
                sub_cat += 1
        if stage_name == 'brand':
            if record['brand'] not in check_brand_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                name = self.env['product.brand'].search([('id', '=', record['brand'])]).name or _(' Not Defined')
                self.get_sub_header(sheet, rowx, _('Brand ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_brand_rowx = rowx
                rowx += 1
                sub_cat += 1
        if stage_name == 'salesman':
            if record['salesman_id'] not in check_salesman_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                name = self.env['res.users'].search([('id', '=', record['salesman_id'])]).name or _(' Not Defined')
                self.get_sub_header(sheet, rowx, _('Salesman ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_salesman_rowx = rowx
                rowx += 1
                sub_cat += 1
        if stage_name == 'salesteam':
            if record['salesteam_id'] not in check_salesteam_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                if record['salesteam_id'] == -1:
                    name = _(' Not Defined')
                else:
                    name = self.env['crm.team'].search([('id', '=', record['salesteam_id'])]).name or _(' Not Defined')
                self.get_sub_header(sheet, rowx, _('Salesteam ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_salesteam_rowx = rowx
                rowx += 1
                sub_cat += 1
        if stage_name == 'customer':
            if record['customer_id'] not in check_customer_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                if record['customer_id'] == -1:
                    name = _(' Not Defined')
                else:
                    name = self.env['res.partner'].search([('id', '=', record['customer_id'])]).name or _(' Not Defined')
                self.get_sub_header(sheet, rowx, _('Customer ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_customer_rowx = rowx
                rowx += 1
                sub_cat += 1
        if stage_name == 'supplier':
            if record['supplier_id'] not in check_supplier_ids:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum \
                    = self._stage_check(state, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum)
                name = self.env['res.partner'].search([('id', '=', record['supplier_id'])]).name or _(' Not Defined')
                self.get_sub_header(sheet, rowx, _('Supplier ') + name, record.get('lot_name', False) if lot != 0 else
                                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, format_content_text_color, format_sub_text_float, True, sale_tax_pay)
                last_supplier_rowx = rowx
                rowx += 1
                sub_cat += 1

        return check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
            warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum, \
            last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx, \
            rowx, sub_cat

    @api.onchange('report_type')
    def onchange_report_type(self):
        self.invis_profit = True if self.report_type not in ('shipment','done') else False

    @api.onchange('warehouse_ids')
    def onchange_warehouse_ids(self):
        loc_ids = []
        stock_setting = []
        """
        Нэвтэрсэн хэрэглэгчийн зөвшөөрөгдсөн агуулах шалгах
        """
        if self.env.user.allowed_warehouse_ids:
            self.env.cr.execute("select * from res_config_settings where company_id = %s order by id DESC LIMIT 1" % self.company_id.id)
            stock_setting = self.env.cr.dictfetchall()
        # Тухайн агуулах дээр тохиргоо байгаа эсэх
        if stock_setting:
            # Агуулахын тохиргоо дээр \Зөвхөн 1 агуулах 1 хадгалах байрлал\ байгаа эсэхийг шалгах
            if stock_setting[0]['group_stock_adv_location'] == False:
                self.invis_location = True
        # Сонгосон агуулахууд
        if self.warehouse_ids:
            for warehouse_id in self.warehouse_ids:
                # Сонгосон агуулах болгоноос байрлалын хаяг авах
                loc_ids.append(warehouse_id.lot_stock_id.id)
            # location_ids талбарлуу домейн буцаах
            return {'domain': {'location_ids': [('id', 'in', loc_ids)]}}
        else:
            return {'domain': {'location_ids': [('id', 'in', False)]}}

    def _solve_single_value(self, list):
        if len(list) == 0:
            list.append(-1)
        if len(list) < 2:
            list.append(-1)
        return list

    # query - гээр мэдээлэл татах
    def _get_query(self, select, _from, where, order_by,  select_two, group_by):
        query = wheree = lot_join = " "
        warehouse_ids, location_ids, category_ids, product_ids, partner_ids, salesman_ids, lot_ids, brand_ids, salesteam_ids, supplier_ids, serial = self._get_wizard_data()
        wheree += """ AND so.warehouse_id in %s AND pt.categ_id in %s AND sw.lot_stock_id in %s """ % (tuple(warehouse_ids), tuple(category_ids), tuple(location_ids))
        if partner_ids:
            wheree += ' AND sol.order_partner_id in (' + ','.join(map(str, partner_ids)) + ')'
        if salesman_ids:
            wheree += ' AND sol.salesman_id in (' + ','.join(map(str, salesman_ids)) + ')'
        if salesteam_ids:
            wheree += ' AND so.team_id in (' + ','.join(map(str, salesteam_ids)) + ')'
        if brand_ids:
            wheree += ' AND pt.brand_id in (' + ','.join(map(str, brand_ids)) + ')'
        if supplier_ids:
            wheree += ' AND pt.supplier_id in (' + ','.join(map(str, supplier_ids)) + ')'
        query += """SELECT
                           pt.default_code as code,pt.type as pt_type,sol.product_id as product_id, pt.name as product_name,
                           sol.purchase_price as standard_price, pu.name as unitname,
                           pt.brand_id as brand,
                           so.partner_id as customer_id, pt.supplier_id as supplier_id, sol.salesman_id as salesman_id, so.team_id as salesteam_id, sol.order_partner_id as partner_id,
                       sw.lot_stock_id as location_id, sw.id as warehouse_id, pt.categ_id as cat_id %s
                       FROM %s 
                           LEFT JOIN product_product pp on pp.id = sol.product_id
                           LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
                           LEFT JOIN uom_uom pu on pu.id = sol.product_uom
                           JOIN sale_order so on so.id = sol.order_id
                           LEFT JOIN sale_category sc on sc.id = so.sale_category_id
                           LEFT JOIN stock_warehouse sw on sw.id = so.warehouse_id
                           %s 
                       WHERE
                           sol.company_id = %s
                           %s AND sol.product_id in %s %s %s """ % (select, _from, lot_join, self.company_id.id, where, tuple(product_ids), serial, wheree )
        query = query
        balanced_query = """SELECT
                               sales_order_report.code as code,  sales_order_report.pt_type as pt_type, sales_order_report.product_name as product_name, SUM(sales_order_report.qty) as qty,
                               SUM(sales_order_report.without_tax_discount) as without_tax_discount, SUM(sales_order_report.tax_discount) as tax_discount,
                               sales_order_report.product_id as product_id, SUM(sales_order_report.standard_price) as standard_price, sales_order_report.unitname as unitname,
                               SUM(sales_order_report.price) as price, SUM(sales_order_report.tax) as tax, SUM(sales_order_report.price_unit) as price_unit,
                                SUM(CASE WHEN (sales_order_report.ref_price <> 0) THEN ((sales_order_report.ref_price)) ELSE 0 END) AS rev_price,
                                SUM(CASE WHEN (sales_order_report.ref_qty <> 0) THEN ((sales_order_report.ref_qty)) ELSE 0 END) AS rev_qty,
                                SUM(CASE WHEN (sales_order_report.ref_tax <> 0) THEN ((sales_order_report.ref_tax)) ELSE 0 END) AS rev_tax  %s
                                          FROM
                                              (%s) as sales_order_report
                                          GROUP BY
                                                sales_order_report.code,
                                                sales_order_report.pt_type,
                                                sales_order_report.product_id,
                                                sales_order_report.product_name,
                                                sales_order_report.unitname
                                                 %s  %s
                                      """ % (select_two, query, group_by, order_by)
        self.env.cr.execute(balanced_query)
        data = self.env.cr.dictfetchall()
        return data

    # Тайлангийн цонхноос өгөгдөл боловсруулах хэсэг
    def _get_wizard_data(self):
        warehouse_ids = []
        location_ids = []
        partner_ids = []
        lot_ids = []
        brand_ids = []
        salesteam_ids = []
        supplier_ids = []
        serial = " "
        # Агуулах сонгосон бол
        if self.warehouse_ids:
            warehouse_ids = self.warehouse_ids.ids
            if self.location_ids:
                location_ids = self.location_ids.ids
            else:
                for warehouse_id in self.warehouse_ids:
                    location_ids.append(warehouse_id.lot_stock_id.id)
        # Агуулах сонгоогүй үед бүх агуулахыг авна
        else:
            if self.env.user.allowed_warehouse_ids:
                for warehouse in self.env.user.allowed_warehouse_ids:
                    warehouse_ids.append(warehouse.id)
                    location_ids.append(warehouse.lot_stock_id.id)
        # Ангилал сонгосон бол
        if self.category_ids:
            category_ids = self.category_ids.ids
            category_ids = self._solve_single_value(category_ids)
        else:
            category_ids = self.env['product.category'].search([]).ids
        # Барааны бренд сонгосон үед
        if self.brand_ids:
            brand_ids = self.brand_ids.ids

        if self.product_ids:
            product_ids = self.product_ids.ids
            product_ids = self._solve_single_value(product_ids)
        else:
            self._cr.execute("""SELECT pp.id FROM product_product pp, product_template pt where pp.product_tmpl_id=pt.id """)
            product_ids = map(lambda x: x[0], self._cr.fetchall())

        # Харилцагч сонгосон үед
        if self.partner_ids:
            partner_ids = self.partner_ids.ids
        # Нийлүүлэгч сонгосон үед
        if self.supplier_ids:
            supplier_ids = self.supplier_ids.ids

        if self.salesperson_ids:
            salesman_ids = self.salesperson_ids.ids
        else:
            self._cr.execute("""SELECT id FROM res_users WHERE company_id = %s """ % (self.company_id.id))
            salesman_ids = map(lambda x: x[0], self._cr.fetchall())
        # Борлуулагтын баг сонгосон үед
        if self.salesteam_ids:
            salesteam_ids = self.salesteam_ids.ids

        if self.see_serial:
            # Цувралтай үед
            if self.lot_ids:
                lot_ids = self.lot_ids.ids
                lot_ids = self._solve_single_value(lot_ids)
                if lot_ids:
                    serial = " OR spl.id in %s " % str(tuple(lot_ids))

        # 1 Утга сонгосон үед гарах алдааг засах
        warehouse_ids = self._solve_single_value(warehouse_ids)
        location_ids = self._solve_single_value(location_ids)
        return warehouse_ids, location_ids, category_ids, product_ids, partner_ids, salesman_ids, lot_ids, brand_ids, salesteam_ids, supplier_ids, serial

    # Тайлангийн бүлэглэлтээс хамааран өгөгдлийг эрэмбэлэх хэсэг
    def _get_order_by_data(self):
        # Бүлэглэх
        order_by = ''
        where = ''
        select = ''
        select_two = ''
        group_by = ''
        warehouse_ids, location_ids, category_ids, product_ids, partner_ids, salesman_ids, lot_ids, brand_ids, salesteam_ids, supplier_ids, serial = self._get_wizard_data()
        if self.stage_one == 'warehouse':
            order_by += ' order by warehouse_id'
            select_two += ", sales_order_report.warehouse_id as warehouse_id"
            group_by += ", sales_order_report.warehouse_id"
        elif self.stage_one == 'location':
            order_by += ' order by location_id'
            select_two += ", sales_order_report.location_id as location_id"
            group_by += ", sales_order_report.location_id"
        elif self.stage_one == 'categ':
            order_by += ' order by cat_id'
            select_two += ", sales_order_report.cat_id as cat_id"
            group_by += ", sales_order_report.cat_id"
        elif self.stage_one == 'brand':
            select_two += ", sales_order_report.brand as brand"
            if brand_ids:
                where += " AND pt.brand_id in %s" % str(tuple(brand_ids))
            order_by += ' order by brand'
            group_by += ", sales_order_report.brand"
        elif self.stage_one == 'salesman':
            if salesman_ids:
                order_by += ' order by salesman_id'
                select_two += ", sales_order_report.salesman_id as salesman_id"
                group_by += ", sales_order_report.salesman_id"
        elif self.stage_one == 'salesteam':
            order_by += ' order by salesteam_id'
            select_two += ", sales_order_report.salesteam_id as salesteam_id"
            group_by += ", sales_order_report.salesteam_id"
        elif self.stage_one == 'customer':
            order_by += ' order by customer_id'
            select_two += ", sales_order_report.customer_id as customer_id"
            group_by += ", sales_order_report.customer_id"
        elif self.stage_one == 'supplier':
            order_by += ' order by supplier_id'
            select_two += ", sales_order_report.supplier_id as supplier_id"
            group_by += ", sales_order_report.supplier_id"
        if self.stage_two == 'warehouse':
            order_by += ', warehouse_id'
            select_two += ", sales_order_report.warehouse_id as warehouse_id"
            group_by += ", sales_order_report.warehouse_id"
        elif self.stage_two == 'location' and not self.invis_location:
            order_by += ', location_id'
            select_two += ", sales_order_report.location_id as location_id"
            group_by += ", sales_order_report.location_id"
        elif self.stage_two == 'categ':
            order_by += ', cat_id'
            select_two += ", sales_order_report.cat_id as cat_id"
            group_by += ", sales_order_report.cat_id"
        elif self.stage_two == 'brand':
            order_by += ', brand'
            select_two += ", sales_order_report.brand as brand"
            if brand_ids:
                where += " AND pt.brand_id in %s" % str(tuple(brand_ids))
            group_by += ", sales_order_report.brand"
        elif self.stage_two == 'salesman':
            if salesman_ids:
                order_by += ', salesman_id'
                select_two += ", sales_order_report.salesman_id as salesman_id"
                group_by += ", sales_order_report.salesman_id"
        elif self.stage_two == 'salesteam':
            order_by += ', salesteam_id'
            select_two += ", sales_order_report.salesteam_id as salesteam_id"
            group_by += ", sales_order_report.salesteam_id"
        elif self.stage_two == 'customer':
            order_by += ', customer_id'
            select_two += ", sales_order_report.customer_id as customer_id"
            group_by += ", sales_order_report.customer_id"
        elif self.stage_two == 'supplier':
            order_by += ', supplier_id'
            select_two += ", sales_order_report.supplier_id as supplier_id"
            group_by += ", sales_order_report.supplier_id"
        if self.stage_three == 'warehouse':
            order_by += ', warehouse_id'
            select_two += ", sales_order_report.warehouse_id as warehouse_id"
            group_by += ", sales_order_report.warehouse_id"
        elif self.stage_three == 'location' and not self.invis_location:
            order_by += ', location_id'
            select_two += ", sales_order_report.location_id as location_id"
            group_by += ", sales_order_report.location_id"
        elif self.stage_three == 'categ':
            order_by += ', cat_id'
            select_two += ", sales_order_report.cat_id as cat_id"
            group_by += ", sales_order_report.cat_id"
        elif self.stage_three == 'brand':
            order_by += ', brand'
            select_two += ", sales_order_report.brand as brand"
            group_by += ", sales_order_report.brand"
            if brand_ids:
                where += " AND pt.brand_id in %s" % str(tuple(brand_ids))
        elif self.stage_three == 'salesman':
            if salesman_ids:
                order_by += ', salesman_id'
                select_two += ", sales_order_report.salesman_id as salesman_id"
                group_by += ", sales_order_report.salesman_id"
        elif self.stage_three == 'salesteam':
            order_by += ', salesteam_id'
            select_two += ", sales_order_report.salesteam_id as salesteam_id"
            group_by += ", sales_order_report.salesteam_id"
        elif self.stage_three == 'customer':
            order_by += ', customer_id'
            select_two += ", sales_order_report.customer_id as customer_id"
            group_by += ", sales_order_report.customer_id"
        elif self.stage_three == 'supplier':
            order_by += ', supplier_id'
            select_two += ", sales_order_report.supplier_id as supplier_id"
            group_by += ", sales_order_report.supplier_id"
        return order_by, select, select_two, where, group_by

    # Тайлангийн бүлэглэлтийн өгөгдлийг цуглуулах
    def _get_append_sub_header(self,record):
        check_ids = []
        check_warehouse_ids = []
        check_location_ids = []
        check_cat_ids = []
        check_brand_ids = []
        check_salesman_ids = []
        check_salesteam_ids = []
        check_customer_ids = []
        check_supplier_ids = []
        check_ids.append(record['product_id'])
        if self.stage_one == 'warehouse':
            check_warehouse_ids.append(record['warehouse_id'])
        elif self.stage_one == 'location_id':
            if not self.invis_location:
                check_location_ids.append(record['location_id'])
        elif self.stage_one == 'categ':
            check_cat_ids.append(record['cat_id'])
        elif self.stage_one == 'brand':
            check_brand_ids.append(record['brand'])
        elif self.stage_one == 'salesman':
            check_salesman_ids.append(record['salesman_id'])
        elif self.stage_one == 'salesteam':
            check_salesteam_ids.append(record['salesteam_id'])
        elif self.stage_one == 'customer':
            check_customer_ids.append(record['customer_id'])
        elif self.stage_one == 'supplier':
            check_supplier_ids.append(record['supplier_id'])
        if self.stage_two == 'warehouse':
            check_warehouse_ids.append(record['warehouse_id'])
        elif self.stage_two == 'location' and not self.invis_location:
            check_location_ids.append(record['location_id'])
        elif self.stage_two == 'categ':
            check_cat_ids.append(record['cat_id'])
        elif self.stage_two == 'brand':
            check_brand_ids.append(record['brand'])
        elif self.stage_two == 'salesman':
            check_salesman_ids.append(record['salesman_id'])
        elif self.stage_two == 'salesteam':
            check_salesteam_ids.append(record['salesteam_id'])
        elif self.stage_two == 'customer':
            check_customer_ids.append(record['customer_id'])
        elif self.stage_two == 'supplier':
            check_supplier_ids.append(record['supplier_id'])
        if self.stage_three == 'warehouse':
            check_warehouse_ids.append(record['warehouse_id'])
        elif self.stage_three == 'location' and not self.invis_location:
            check_location_ids.append(record['location_id'])
        elif self.stage_three == 'categ':
            check_cat_ids.append(record['cat_id'])
        elif self.stage_three == 'brand':
            check_brand_ids.append(record['brand'])
        elif self.stage_three == 'salesman':
            check_salesman_ids.append(record['salesman_id'])
        elif self.stage_three == 'salesteam':
            check_salesteam_ids.append(record['salesteam_id'])
        elif self.stage_three == 'customer':
            check_customer_ids.append(record['customer_id'])
        elif self.stage_three == 'supplier':
            check_supplier_ids.append(record['supplier_id'])

        return check_ids, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids

    # Тайлан дээр гарах өгөгдөл татах хэсэг
    def get_data(self):
        _from = ''
        order_by, select, select_two, where, group_by = self._get_order_by_data()
        datetime_from_str = str(get_day_by_user_timezone(str(self.date_from) + ' 00:00:00', self.env.user))
        datetime_to_str = str(get_day_by_user_timezone(str(self.date_to) + ' 23:59:59', self.env.user))

        # Тайлангын сонгосон төрлөөс хамааруулан өгөгдлүүдийг тооцно
        if self.report_type == 'sales order' or self.report_type == 'loan': # Тайлангийн төрөл нь Борлуулалтын захиалга эсвэл Зээлээр төрөлтэй тайлангийн тооцоолол
            """Үйлчилгээ төрөлтэй бараа үед нэхэмжлэлээс буцаалтыг тооцно"""
            select = ", sol.price_unit as price_unit, so.picking_policy as type, sol.product_uom_qty as qty, sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal as without_tax_discount, " \
                        "CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal) ELSE 0 END as tax_discount, 0 AS sub_total_price , " \
                        "CASE WHEN (sol.price_subtotal <> 0) THEN (sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal) ELSE 0 END AS tax, " \
                        "sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) AS price, " \
                        "(((CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *  ail.quantity) ELSE 0 END) ELSE 0 END) - " \
                        "(CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty * ail.quantity) ELSE 0 END) ELSE 0 END))) / NULLIF(ail.quantity,0) * table1.qty AS ref_tax, " \
                    "table1.price_unit as ref_price, table1.qty as ref_qty "
            select_two += ", SUM(sales_order_report.sub_total_price) as sub_total_price"
            _from = " sale_order_line sol " \
                    "INNER JOIN sale_order_line_invoice_rel solir on solir.order_line_id = sol.id " \
                    "INNER JOIN account_move_line ail on ail.id = solir.invoice_line_id " \
                    "LEFT JOIN account_move ai on ai.id = ail.move_id " \
                    "LEFT JOIN " \
                    "(SELECT ref_ai.reversed_entry_id as refund_invoice_id, ref_ail.price_unit as price_unit,  ref_ail.quantity as qty, ref_ail.product_id as product_id, ref_ail.price_subtotal as ref_price_subtotal " \
                    "FROM account_move ref_ai " \
                    "LEFT JOIN account_move_line ref_ail on ref_ail.move_id = ref_ai.id " \
                    "WHERE ref_ai.payment_state in ('in_payment', 'paid'))  table1 on table1.refund_invoice_id = ai.id and ai.reversed_entry_id is null and sol.product_id = table1.product_id "
            where = " AND sol.state in ('done','sale')  AND pt.type='service'  AND so.date_order BETWEEN '" + datetime_from_str + "' AND '" + datetime_to_str +"' "
            if self.report_type == 'loan':
                where += " AND sc.is_loan = 't'"
            data1 = self._get_query(select, _from, where, order_by, select_two, group_by)
            """Хадгалах төрөлтэй бараа үед агуулахын хөдөлгөөнөөс буцаалтыг тооцно"""
            select = ", sol.price_unit as price_unit, sol.product_uom_qty as qty, sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal as without_tax_discount, " \
                        "CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)  - sol.price_subtotal) * sol.price_tax/sol.price_subtotal) ELSE 0 END as tax_discount, 0 AS sub_total_price , " \
                        "CASE WHEN (sol.price_subtotal <> 0) THEN (sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) * sol.price_tax/sol.price_subtotal) ELSE 0 END AS tax, " \
                        "sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) AS price, " \
                        "(CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(1-sol.discount/100)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *table1.qty) ELSE 0 END)- (CASE WHEN (sol.price_subtotal <> 0) THEN (((sol.price_subtotal/(1-sol.discount/100) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *table1.qty) ELSE 0 END) AS ref_tax, " \
                        "((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)) - (sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal))/NULLIF(sol.product_uom_qty,0) *table1.qty  AS ref_price,  " \
                        "table1.qty as ref_qty  "
            select_two += ", SUM(sales_order_report.sub_total_price) as sub_total_price"
            _from = " sale_order_line sol "\
                    "LEFT JOIN " \
                    "(SELECT sm1.sale_line_id as sale_line_id, sm1.product_uom_qty as qty, sm1.product_id as product_id " \
                    "FROM stock_move sm1 " \
                    "WHERE sm1.state = 'done' and sm1.origin_returned_move_id is not null) table1 on table1.sale_line_id = sol.id and sol.product_id = table1.product_id "
            where = " AND sol.state in ('done','sale')  AND pt.type <> 'service' AND so.date_order BETWEEN '" + datetime_from_str + "' AND '" + datetime_to_str +"'"
            if self.report_type == 'loan':
                where += " AND sc.is_loan = 't'"
            data2 = self._get_query(select, _from, where, order_by, select_two, group_by)
            data = data1 + data2
        elif self.report_type == 'invoice': # Тайлангийн төрөл нь Нэхэмжлэлээр төрөлтэй тайлангийн тооцоолол
            select = ",ail.price_unit as price_unit,  ail.quantity as qty, 0 AS sub_total_price , " \
                    "CASE WHEN (ail.quantity <> 0) THEN ((ail.price_subtotal / (CASE WHEN (1-ail.discount/100) <> 0 THEN (1-ail.discount/100) ELSE 1 END) - ail.price_subtotal)/ail.quantity * ail.quantity) ELSE 0 END AS without_tax_discount, " \
                    "CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/NULLIF(sol.product_uom_qty,0) * ail.quantity) ELSE 0 END) ELSE 0 END AS tax_discount, " \
                    "CASE WHEN (ail.quantity <> 0) THEN ((ail.price_subtotal/(CASE WHEN (1-ail.discount/100) <> 0 THEN (1-ail.discount/100) ELSE 1 END))/ail.quantity * ail.quantity) ELSE 0 END AS price, " \
                    "CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/ NULLIF(sol.product_uom_qty,0) * ail.quantity) ELSE 0 END) ELSE 0 END AS tax, " \
                    "table1.ref_price_subtotal AS ref_price, table1.qty as ref_qty, " \
                    "(((CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *  ail.quantity) ELSE 0 END) ELSE 0 END) - " \
                    "(CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty * ail.quantity) ELSE 0 END) ELSE 0 END))) / NULLIF(ail.quantity,0) * table1.qty AS ref_tax "
            select_two += ", SUM(sales_order_report.sub_total_price) as sub_total_price"
            _from = " account_move_line ail " \
                    "INNER JOIN sale_order_line_invoice_rel solir on solir.invoice_line_id = ail.id " \
                    "INNER JOIN sale_order_line sol on sol.id = solir.order_line_id " \
                    "LEFT JOIN account_move ai on ai.id = ail.move_id " \
                    "LEFT JOIN " \
                    "(SELECT ref_ai.reversed_entry_id as refund_invoice_id, ref_ail.price_subtotal/(1-ref_ail.discount/100) as ref_price, ref_ail.price_subtotal as ref_price_subtotal,"\
                    " ref_ail.discount as ref_discount,ref_ail.quantity as qty, ref_ail.product_id as product_id " \
                    "FROM account_move ref_ai " \
                    "LEFT JOIN account_move_line ref_ail on ref_ail.move_id = ref_ai.id " \
                    "WHERE ref_ai.payment_state in ('in_payment', 'paid'))  table1 on table1.refund_invoice_id = ai.id and ai.reversed_entry_id is null and sol.product_id = table1.product_id "
            where = " AND ai.payment_state in ('in_payment', 'paid') AND ai.invoice_date BETWEEN '" + datetime_from_str + "' AND '" + datetime_to_str +"'"
            data = self._get_query(select, _from, where, order_by, select_two, group_by)
        elif self.report_type == 'shipment': # Тайлангийн төрөл нь Тээвэрлэлтээр төрөлтэй тайлангийн тооцоолол
            select += ", sol.price_unit as price_unit, sm.product_uom_qty as qty," \
                    "CASE WHEN ((sol.product_uom_qty <> 0 or table1.qty <> 0) and sm.origin_returned_move_id is null and sol.product_uom_qty > 0) THEN ((sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)- sol.price_subtotal)/sol.product_uom_qty*sm.product_uom_qty) ELSE 0 END AS without_tax_discount, " \
                    "CASE WHEN ((sol.product_uom_qty <> 0 or table1.qty <> 0) and sm.origin_returned_move_id is null and sol.product_uom_qty > 0) THEN (CASE WHEN (sol.product_uom_qty <> 0 and sol.price_subtotal <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty*sm.product_uom_qty) ELSE 0 END) ELSE 0 END AS tax_discount, " \
                    "CASE WHEN (sol.product_uom_qty <> 0 and sm.origin_returned_move_id is null) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END))/sol.product_uom_qty * sm.product_uom_qty) ELSE 0 END AS price, " \
                    "CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty * sm.product_uom_qty) ELSE 0 END) ELSE 0 END AS tax, " \
                    "(CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *table1.qty) ELSE 0 END)- (CASE WHEN (sol.price_subtotal <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *table1.qty) ELSE 0 END) AS ref_tax, " \
                    "((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)) - (sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal))/sol.product_uom_qty *table1.qty  AS ref_price, " \
                    "table1.price_unit as ref_price_unit, table1.qty as ref_qty "
            if self.see_profit:
                select += ", CASE WHEN (table1.qty > 0) THEN ((sm.price_unit * sm.product_uom_qty) - (table1.price_unit * table1.qty)) ELSE sm.price_unit * sm.product_uom_qty END AS sub_total_price  "
                select_two += ", SUM(sales_order_report.sub_total_price) as sub_total_price"
            _from = " stock_move sm LEFT JOIN sale_order_line sol on sol.id = sm.sale_line_id "
            if self.see_serial:
                select += ",spl.name as lot_name , spl.id as lot_id "
                _from += "LEFT JOIN stock_move_line sml on sml.picking_id = sm.picking_id " \
                         "LEFT JOIN stock_production_lot spl on spl.id = sml.lot_id "
            _from += "LEFT JOIN " \
                    "(SELECT sm1.origin_returned_move_id as origin_returned_move_id, sm1.product_uom_qty as qty, sm1.price_unit as price_unit, sm1.product_id as product_id " \
                    "FROM stock_move sm1 " \
                    "WHERE sm1.state = 'done')  table1 on table1.origin_returned_move_id = sm.id and sm.origin_returned_move_id is null and sm.product_id = table1.product_id "
            where = " AND sm.origin_returned_move_id is null AND sm.state = 'done' AND sm.date BETWEEN '" + datetime_from_str + "' AND '" + datetime_to_str + "'"
            if self.see_serial:
                where += " AND sml.product_id = sm.product_id "
                select_two += """,sales_order_report.lot_id as lot_id, sales_order_report.lot_name as lot_name """
                group_by += """ , sales_order_report.lot_id, sales_order_report.lot_name  """

            data = self._get_query(select, _from, where, order_by, select_two, group_by)
        else: #Тайлангийн төрөл дууссанг сонгоход нэхэмжлэл төлөгдсөн болон агуулахын хөдөлгөөн хийгдсэн төлөвтэй борлуулалтын захиалгуудыг харуулна.
            """Үйлчилгээ төрөлтэй бараа үед нэхэмжлэлээс буцаалтыг тооцно"""
            select = ",ail.price_unit as price_unit,  ail.quantity as qty, 0 AS sub_total_price , " \
                    "CASE WHEN (ail.quantity <> 0) THEN ((ail.price_subtotal / (1-ail.discount/100) - ail.price_subtotal)/ail.quantity * ail.quantity) ELSE 0 END AS without_tax_discount, " \
                    "CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/NULLIF(sol.product_uom_qty,0) * ail.quantity) ELSE 0 END) ELSE 0 END AS tax_discount, " \
                    "CASE WHEN (ail.quantity <> 0) THEN ((ail.price_subtotal/(1-ail.discount/100))/ail.quantity * ail.quantity) ELSE 0 END AS price, " \
                    "CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/NULLIF(sol.product_uom_qty,0) * ail.quantity) ELSE 0 END) ELSE 0 END AS tax, " \
                    "table1.ref_price_subtotal AS ref_price, table1.qty as ref_qty, " \
                    "(((CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *  ail.quantity) ELSE 0 END) ELSE 0 END) - " \
                    "(CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty * ail.quantity) ELSE 0 END) ELSE 0 END))) / ail.quantity * table1.qty AS ref_tax "
            if self.see_profit:
                select_two += ", SUM(sales_order_report.sub_total_price) as sub_total_price"
            _from = " sale_order_line sol " \
                    "INNER JOIN sale_order_line_invoice_rel solir on solir.order_line_id = sol.id " \
                    "INNER JOIN account_move_line ail on ail.id = solir.invoice_line_id " \
                    "LEFT JOIN account_move ai on ai.id = ail.move_id " \
                    "LEFT JOIN " \
                    "(SELECT ref_ai.reversed_entry_id as refund_invoice_id, ref_ail.price_subtotal/(1-ref_ail.discount/100) as ref_price, ref_ail.price_subtotal as ref_price_subtotal,"\
                    " ref_ail.discount as ref_discount,ref_ail.quantity as qty, ref_ail.product_id as product_id " \
                    "FROM account_move ref_ai " \
                    "LEFT JOIN account_move_line ref_ail on ref_ail.move_id = ref_ai.id " \
                    "WHERE ref_ai.payment_state in ('paid'))  table1 on table1.refund_invoice_id = ai.id and ai.reversed_entry_id is null and sol.product_id = table1.product_id "
            where = " AND ai.payment_state in ('paid') AND pt.type='service' AND so.date_order BETWEEN '" + datetime_from_str + "' AND '" + datetime_to_str +"' "
            data1 = self._get_query(select, _from, where, order_by, select_two, group_by)
            """Хадгалах төрөлтэй бараа үед агуулахын хөдөлгөөнөөс буцаалтыг тооцно"""
            select = ", sol.price_unit as price_unit, sm.product_uom_qty as qty," \
                    "CASE WHEN (sol.product_uom_qty <> 0 or table1.qty <> 0) THEN ((sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal)/sol.product_uom_qty*sm.product_uom_qty) ELSE 0 END AS without_tax_discount, " \
                    "CASE WHEN (sol.price_subtotal <> 0 or table1.qty <> 0) THEN (CASE WHEN (sol.product_uom_qty <> 0 and sol.price_subtotal <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/sol.product_uom_qty*sm.product_uom_qty) ELSE 0 END) ELSE 0 END AS tax_discount, " \
                    "CASE WHEN (sol.product_uom_qty <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END))/sol.product_uom_qty * sm.product_uom_qty) ELSE 0 END AS price, " \
                    "CASE WHEN (sol.price_subtotal <> 0) THEN (CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/NULLIF(sol.product_uom_qty,0) * sm.product_uom_qty) ELSE 0 END) ELSE 0 END AS tax, " \
                    "(CASE WHEN (sol.price_subtotal <> 0) THEN ((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)*sol.price_tax/sol.price_subtotal)/sol.product_uom_qty *table1.qty) ELSE 0 END)- (CASE WHEN (sol.price_subtotal <> 0) THEN (((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal) * sol.price_tax/sol.price_subtotal)/NULLIF(sol.product_uom_qty,0) *table1.qty) ELSE 0 END) AS ref_tax, " \
                    "((sol.price_subtotal/(CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END)) - (sol.price_subtotal / (CASE WHEN (1-sol.discount/100) <> 0 THEN (1-sol.discount/100) ELSE 1 END) - sol.price_subtotal))/NULLIF(sol.product_uom_qty,0) *table1.qty  AS ref_price,  " \
                    "table1.price_unit as ref_price_unit, table1.qty as ref_qty, CASE WHEN (table1.qty > 0) THEN ((sm.price_unit * sm.product_uom_qty) - (table1.price_unit * table1.qty)) ELSE sm.price_unit * sm.product_uom_qty END AS sub_total_price "
            if self.see_profit:
                select_two += ", SUM(sales_order_report.sub_total_price) as sub_total_price"
            _from = " stock_move sm " \
                    "LEFT JOIN sale_order_line sol on sol.id = sm.sale_line_id " \
                    "INNER JOIN sale_order_line_invoice_rel solir on solir.order_line_id = sol.id " \
                    "INNER JOIN account_move_line ail on ail.id = solir.invoice_line_id " \
                    "LEFT JOIN account_move ai on ai.id = ail.move_id "
            if self.see_serial:
                select += ",spl.name as lot_name , spl.id as lot_id "
                _from += "LEFT JOIN stock_move_line sml on sml.picking_id = sm.picking_id " \
                         "LEFT JOIN stock_production_lot spl on spl.id = sml.lot_id "
            _from += "LEFT JOIN " \
                    "(SELECT sm1.origin_returned_move_id as origin_returned_move_id, sm1.product_uom_qty as qty, sm1.price_unit as price_unit, sm1.product_id as product_id " \
                    "FROM stock_move sm1 " \
                    "WHERE sm1.state = 'done')  table1 on table1.origin_returned_move_id = sm.id and sm.origin_returned_move_id is null and sm.product_id = table1.product_id "
            where = "  AND ai.payment_state in ('paid') AND pt.type<>'service' AND sm.origin_returned_move_id is null  AND sm.state = 'done' AND sm.date BETWEEN '" + datetime_from_str + "' AND '" + datetime_to_str +"'"
            if self.see_serial:
                where += " AND sml.product_id = sm.product_id "
                select_two += """,sales_order_report.lot_id as lot_id, sales_order_report.lot_name as lot_name """
                group_by += """ , sales_order_report.lot_id, sales_order_report.lot_name  """
            data2 = self._get_query(select, _from, where, order_by, select_two, group_by)
            data = data1 + data2
        return data

    # Тайлангийн дэд гарчгууд
    def get_dict(self):

        warehouse_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                         'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                         'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        location_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                        'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                        'net_total': 0, 'net_cost_price': 0, 'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        cat_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                   'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                   'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        brand_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                     'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                     'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        salesman_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                        'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                        'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        salesteam_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                         'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                         'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        customer_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                        'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                        'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        supplier_sum = {'qty': 0, 'sub_total': 0, 'tax': 0, 'total': 0, 'without_tax_discount': 0, 'tax_discount': 0, 'with_tax_discount': 0, 'rev_qty': 0, 'rev_sub_total': 0,
                        'rev_tax': 0, 'rev_total': 0, 'net_qty': 0, 'net_sub_total': 0, 'net_tax': 0,
                        'net_total': 0, 'net_cost_price': 0,  'unit_price': 0, 'net_profit': 0, 'profit_of_unit': 0, 'percent': 0}
        return warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum

        # Тайлангийн дэд гарчигийн нийлбэр
    def get_sum_dict(self, sheet, record, warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount, \
                        rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price, net_tax, net_price_tax, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent,  last_ware_rowx, \
                        last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx, lot, sale_tax_pay, format_title, format_sub_text_float ):
            warehouse_sum = self._fill_sum_value(warehouse_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                                 rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price,
                                                 net_tax, net_price_tax, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent)
            location_sum = self._fill_sum_value(location_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                                rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price,
                                                net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)
            cat_sum = self._fill_sum_value(cat_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                           rev_qty, rev_price, rev_tax, rev_price_tax, net_qty,
                                           net_price, net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)
            brand_sum = self._fill_sum_value(brand_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                             rev_qty, rev_price, rev_tax, rev_price_tax, net_qty,
                                             net_price, net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)
            salesman_sum = self._fill_sum_value(salesman_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                                rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price,
                                                net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)
            salesteam_sum = self._fill_sum_value(salesteam_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                                 rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price,
                                                 net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)
            customer_sum = self._fill_sum_value(customer_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                                rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price,
                                                net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)
            supplier_sum = self._fill_sum_value(supplier_sum, sale_qty, price, tax, price_tax, without_tax_discount, tax_discount, with_tax_discount,
                                                rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price,
                                                net_tax, net_price_tax, net_cost_price,  cost_price_unit, net_profit, profit_of_unit, percent)

            if last_ware_rowx != -1:
                self.get_sub_header(sheet, last_ware_rowx, '', record['lot_name'] if lot != 0 else '', warehouse_sum['qty'],
                                        warehouse_sum['sub_total'], warehouse_sum['tax'], warehouse_sum['total'], warehouse_sum['without_tax_discount'], warehouse_sum['tax_discount'], warehouse_sum['with_tax_discount'],
                                        warehouse_sum['rev_qty'], warehouse_sum['rev_sub_total'], warehouse_sum['rev_tax'], warehouse_sum['rev_total'],
                                        warehouse_sum['net_qty'], warehouse_sum['net_sub_total'], warehouse_sum['net_tax'], warehouse_sum['net_total'], warehouse_sum['net_cost_price'],
                                        warehouse_sum['unit_price'], warehouse_sum['net_profit'], warehouse_sum['profit_of_unit'], warehouse_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            if last_location_rowx != -1:
                self.get_sub_header(sheet, last_location_rowx, '', record['lot_name'] if lot != 0 else '', location_sum['qty'],
                                        location_sum['sub_total'], location_sum['tax'],location_sum['total'], location_sum['without_tax_discount'], location_sum['tax_discount'], location_sum['with_tax_discount'],
                                        location_sum['rev_qty'], location_sum['rev_sub_total'], location_sum['rev_tax'], location_sum['rev_total'],
                                        location_sum['net_qty'], location_sum['net_sub_total'], location_sum['net_tax'], location_sum['net_total'], location_sum['net_cost_price'],
                                        location_sum['unit_price'], location_sum['net_profit'], location_sum['profit_of_unit'], location_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            if last_cat_rowx != -1:
                self.get_sub_header(sheet, last_cat_rowx, '', record['lot_name'] if lot != 0 else '', cat_sum['qty'],
                                        cat_sum['sub_total'], cat_sum['tax'], cat_sum['total'], cat_sum['without_tax_discount'], cat_sum['tax_discount'], cat_sum['with_tax_discount'],
                                        cat_sum['rev_qty'], cat_sum['rev_sub_total'],cat_sum['rev_tax'], cat_sum['rev_total'],
                                        cat_sum['net_qty'], cat_sum['net_sub_total'], cat_sum['net_tax'], cat_sum['net_total'], cat_sum['net_cost_price'],
                                        cat_sum['unit_price'], cat_sum['net_profit'], cat_sum['profit_of_unit'], cat_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            if last_brand_rowx != -1:
                self.get_sub_header(sheet, last_brand_rowx, '', record['lot_name'] if lot != 0 else '', brand_sum['qty'],
                                        brand_sum['sub_total'], brand_sum['tax'], brand_sum['total'], brand_sum['without_tax_discount'], brand_sum['tax_discount'], brand_sum['with_tax_discount'],
                                        brand_sum['rev_qty'], brand_sum['rev_sub_total'], brand_sum['rev_tax'], brand_sum['rev_total'],
                                        brand_sum['net_qty'], brand_sum['net_sub_total'], brand_sum['net_tax'], brand_sum['net_total'], brand_sum['net_cost_price'],
                                        brand_sum['unit_price'], brand_sum['net_profit'], brand_sum['profit_of_unit'], brand_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)

            if last_salesman_rowx != -1:
                self.get_sub_header(sheet, last_salesman_rowx, '', record['lot_name'] if lot != 0 else '', salesman_sum['qty'],
                                        salesman_sum['sub_total'], salesman_sum['tax'], salesman_sum['total'], salesman_sum['without_tax_discount'], salesman_sum['tax_discount'], salesman_sum['with_tax_discount'],
                                        salesman_sum['rev_qty'], salesman_sum['rev_sub_total'], salesman_sum['rev_tax'], salesman_sum['rev_total'],
                                        salesman_sum['net_qty'], salesman_sum['net_sub_total'], salesman_sum['net_tax'], salesman_sum['net_total'], salesman_sum['net_cost_price'],
                                        salesman_sum['unit_price'], salesman_sum['net_profit'], salesman_sum['profit_of_unit'], salesman_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            if last_salesteam_rowx != -1:
                self.get_sub_header(sheet, last_salesteam_rowx, '', record['lot_name'] if lot != 0 else '', salesteam_sum['qty'],
                                        salesteam_sum['sub_total'], salesteam_sum['tax'], salesteam_sum['total'], salesteam_sum['without_tax_discount'], salesteam_sum['tax_discount'], salesteam_sum['with_tax_discount'],
                                        salesteam_sum['rev_qty'], salesteam_sum['rev_sub_total'], salesteam_sum['rev_tax'], salesteam_sum['rev_total'],
                                        salesteam_sum['net_qty'], salesteam_sum['net_sub_total'], salesteam_sum['net_tax'], salesteam_sum['net_total'], salesteam_sum['net_cost_price'],
                                        salesteam_sum['unit_price'], salesteam_sum['net_profit'], salesteam_sum['profit_of_unit'], salesteam_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            if last_customer_rowx != -1:
                self.get_sub_header(sheet, last_customer_rowx, '', record['lot_name'] if lot != 0 else '', customer_sum['qty'],
                                        customer_sum['sub_total'], customer_sum['tax'], customer_sum['total'], customer_sum['without_tax_discount'], customer_sum['tax_discount'], customer_sum['with_tax_discount'],
                                        customer_sum['rev_qty'], customer_sum['rev_sub_total'], customer_sum['rev_tax'], customer_sum['rev_total'],
                                        customer_sum['net_qty'], customer_sum['net_sub_total'], customer_sum['net_tax'], customer_sum['net_total'], customer_sum['net_cost_price'],
                                        customer_sum['unit_price'], customer_sum['net_profit'], customer_sum['profit_of_unit'], customer_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            if last_supplier_rowx != -1:
                self.get_sub_header(sheet, last_supplier_rowx, '', record['lot_name'] if lot != 0 else '', supplier_sum['qty'],
                                        supplier_sum['sub_total'], supplier_sum['tax'], supplier_sum['total'], supplier_sum['without_tax_discount'], supplier_sum['tax_discount'], supplier_sum['with_tax_discount'],
                                        supplier_sum['rev_qty'], supplier_sum['rev_sub_total'], supplier_sum['rev_tax'], supplier_sum['rev_total'],
                                        supplier_sum['net_qty'], supplier_sum['net_sub_total'], supplier_sum['net_tax'], supplier_sum['net_total'], supplier_sum['net_cost_price'],
                                        supplier_sum['unit_price'], supplier_sum['net_profit'], supplier_sum['profit_of_unit'], supplier_sum['percent'], format_title, format_sub_text_float, False, sale_tax_pay)
            return sheet

    #Тайлангийн тоон утгыг боловсруулан зурах хэсэг
    def compute_data(self, sheet, rowx, seq, temp, record, format_content_center, format_content_left, format_content_text, format_content_float, format_red_text, lot, sale_tax_pay, check_ids, sub_cat,total_qty, total_price, total_tax, total_price_tax, total_without_tax_discount, total_tax_discount, total_with_tax_discount, total_rev_qty, total_rev_price, total_rev_tax,total_rev_price_tax, net_total_qty, total_price_net, total_tax_net, total_price_tax_net, total_purchase_cost_row, total_standard_cost, key, colx_to_start=0 ):
        alp_col_list = ['E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        counter = 0
        serial_seq = seq
        is_first = True  # Эхний утга шалгах хувьсагч
        is_solo = False  # Дан утга шалгах хувьсагч
        before_value = {'code': '',
                        'name': '',
                        'product_id': 0}
        # Цувралгүй үед
        if key:
            colx = 0
        if lot == 0:
            colx = colx
            sheet.write(rowx, colx, '%s' % (seq), format_content_center)
            colx += 1
            sheet.write(rowx, colx, record['code'], format_content_center)
            colx += 1
            sheet.write(rowx, colx, record['product_name'], format_content_left)
            colx += 1
        # Цувралтай үед
        else:
            # 2 дахь утга
            if not is_first:
                # Ялгаатай бараа ирэх үед
                if record['product_id'] not in check_ids:
                    del check_ids[:]
                    # Дан утга биш үед
                    if not is_solo:
                        sheet.merge_range(rowx - counter - sub_cat, 0, rowx - 1 - sub_cat, 0, serial_seq, format_content_center)
                        sheet.merge_range(rowx - counter - sub_cat, 1, rowx - 1 - sub_cat, 1, before_value['code'], format_content_center)
                        sheet.merge_range(rowx - counter - sub_cat, 2, rowx - 1 - sub_cat, 2, before_value['name'] + '(' + str(counter) + ')', format_content_text)
                        serial_seq += 1
                    # Дан утга үед
                    else:
                        sheet.write(rowx - 1 - sub_cat, 0, serial_seq, format_content_center)
                        sheet.write(rowx - 1 - sub_cat, 1, before_value['code'], format_content_center)
                        sheet.write(rowx - 1 - sub_cat, 2, before_value['name'], format_content_text)
                        serial_seq += 1
                    is_solo = True
                    counter = 1
                # Ижил бараа байх үед
                else:
                    counter += 1
                    is_solo = False
                colx = 3
            # Эхний утга
            else:
                colx = 3
                sheet.write(rowx, 0, serial_seq, format_content_center)
                sheet.write(rowx, 1, record['code'], format_content_center)
                sheet.write(rowx, 2, record['product_name'], format_content_left)
                counter += 1
                is_first = False
        # Хэмжих нэгжээс эхлэн бүгд ижил шивнэ
        sheet.write(rowx, colx, record['unitname'], format_content_center)
        colx += 1
        # Цуврал бүгд
        if lot == 2:
            sheet.write(rowx, colx, record['lot_name'], format_content_center)
            colx += 1
        # Цувралаас сонгосон үед
        elif lot == 1:
            for prod in self.lot_ids:
                # Цувралд утга байгаа үед
                if record['lot_id']:
                    if record['lot_id'] == prod.id:
                        sheet.write(rowx, colx, record['lot_name'], format_content_center)
                    else:
                        sheet.write(rowx, colx, record['lot_name'], format_content_center)
                # Цувралд утга байхгүй үед
                else:
                    sheet.write(rowx, colx, record['lot_name'], format_content_center)
            colx += 1
        qty =  record['qty'] if 'qty' in record else 0
        price = record['price'] if 'price' in record else 0
        tax = record['tax'] if 'tax' in record else 0
        if not tax:
            tax = 0
        price_tax = price + tax
        without_tax_discount = record['without_tax_discount'] if record['without_tax_discount'] else 0
        tax_discount =  record['tax_discount'] if record['tax_discount'] else 0
        with_tax_discount = without_tax_discount + tax_discount

        #Буцаалт
        rev_qty = record['rev_qty']
        rev_price = record['rev_price']
        rev_tax = record['rev_tax']
        rev_price_tax = rev_price + rev_tax
        # Борлуулалт
        sale_qty = qty
        sale_price = price if price > 0 else 0
        sale_tax = tax if tax > 0 else 0
        sale_price_tax = price_tax if price_tax > 0 else 0
        pt_type = record['pt_type']
        if colx_to_start:
            colx = colx_to_start
        else:
            colx = 5 if self.see_serial else 4

        sheet.write(rowx, colx, sale_qty, format_content_float)
        colx += 1

        if not sale_tax_pay:
            sheet.write(rowx, colx, sale_price, format_content_float) # Борлуулалт НӨАТ-гүй дүн
            colx+=1
            sheet.write(rowx, colx, sale_tax, format_content_float) # Борлуулалт НӨАТ '{='+alp_col_list[1+temp]+str(rowx+1)+'*0.1}' зарим нь татваргүй байж болзошгүй тул
            colx+=1
            sheet.write_formula(rowx, colx, '{='+alp_col_list[1+temp]+str(rowx+1)+'+'+alp_col_list[2+temp]+str(rowx+1)+'}', format_content_float) # Борлуулалт НӨАТ-тэй дүн sale_price_tax
            colx+=1
        else:
            sheet.write(rowx, colx, sale_price + sale_tax, format_content_float)
            colx+=1
        if not sale_tax_pay:
            sheet.write(rowx, colx, without_tax_discount, format_content_float) # Борлуулалт Хөнгөлөлт (НӨАТ-гүй)
            colx+=1
            sheet.write(rowx, colx, tax_discount, format_content_float) # Борлуулалт Хөнгөлөлт (НӨАТ)
            colx+=1
            sheet.write_formula(rowx, colx, '{=' + alp_col_list[4 + temp] + str(rowx + 1) + '+' + alp_col_list[
                5 + temp] + str(rowx + 1) + '}', format_content_float)  #Борлуулалт Хөнгөлөлт (НӨАТ-тэй)
            colx+=1
        else:
            sheet.write(rowx, colx, without_tax_discount + tax_discount, format_content_float)
            colx+=1

        sheet.write(rowx, colx, rev_qty, format_content_float) # Буцаалт Тоо
        colx += 1
        if not sale_tax_pay:
            sheet.write(rowx, colx, rev_price, format_content_float)  # Буцаалт НӨАТ-гүй дүн
            colx += 1
            sheet.write(rowx, colx, rev_tax, format_content_float)  # Буцаалт НӨАТ
            colx += 1
            sheet.write_formula(rowx, colx, '{=' + alp_col_list[8 + temp] + str(rowx + 1) + '+' + alp_col_list[
                9 + temp] + str(rowx + 1) + '}', format_content_float)  # Буцаалт НӨАТ-тай дүн rev_price_tax
            colx += 1
        else:
            sheet.write(rowx, colx, rev_price + rev_tax, format_content_float)
            colx+=1
        # Цэвэр борлуулалт /буцаалтыг хасаад цэвэр ашиг гарна/
        if not sale_tax_pay:
            sheet.write_formula(rowx, colx, '{='+alp_col_list[0+temp]+str(rowx+1)+'-'+alp_col_list[7+temp]+str(rowx+1)+'}', format_content_float)# Цэвэр борлуулалт Тоо
            colx+=1
        else:
            sheet.write_formula(rowx, colx, '{='+alp_col_list[0+temp]+str(rowx+1)+'-'+alp_col_list[4+temp]+str(rowx+1)+'}', format_content_float)# Цэвэр борлуулалт Тоо
            colx+=1

        if not sale_tax_pay:
            sheet.write_formula(rowx, colx, '{='+alp_col_list[1+temp]+str(rowx+1)+'-'+alp_col_list[4+temp]+str(rowx+1)+'-'+alp_col_list[8+temp]+str(rowx+1)+'}', format_content_float) # Цэвэр борлуулалт НӨАТ-гүй дүн
            colx+=1
            sheet.write_formula(rowx, colx, '{='+alp_col_list[2+temp]+str(rowx+1)+'-'+alp_col_list[5+temp]+str(rowx+1)+'-'+alp_col_list[9+temp]+str(rowx+1)+'}', format_content_float)# Цэвэр борлуулалт НӨАТ
            colx+=1
            sheet.write_formula(rowx, colx, '{='+alp_col_list[12+temp]+str(rowx+1)+'+'+alp_col_list[13+temp]+str(rowx+1)+'}', format_content_float) # Цэвэр борлуулалт НӨАТ-тай дүн
            colx+=1
        else:
            sheet.write(rowx, colx, (sale_price + sale_tax) - (without_tax_discount + tax_discount) - rev_price + rev_tax, format_content_float) # Цэвэр борлуулалт НӨАТ-тай дүн
            colx+=1

        # Нийт дүнгээс хөнгөлөлт болон буцаалтын нийт дүнг хасна
        net_qty = 1 if sale_qty == 0 else sale_qty - rev_qty # 0-д хувааж болохгүй
        net_price_tax = sale_price_tax - rev_price_tax
        net_price = price
        net_tax = tax

        # count parametr
        total_qty += sale_qty
        total_price += sale_price
        total_tax += sale_tax
        total_price_tax += sale_price_tax
        total_without_tax_discount += without_tax_discount
        total_tax_discount += tax_discount
        total_with_tax_discount = total_without_tax_discount + total_tax_discount

        # Буцаалт
        total_rev_qty += rev_qty
        total_rev_price += rev_price
        total_rev_tax += rev_tax
        total_rev_price_tax += rev_price_tax

        #Цэвэр ашиг
        net_total_qty = total_qty - total_rev_qty
        total_price_net = total_price - total_rev_price - total_without_tax_discount
        total_tax_net = total_tax - total_rev_tax - total_tax_discount
        total_price_tax_net = total_price_tax - total_rev_price_tax - total_with_tax_discount

        # Ашиг
        net_cost_price = cost_price_unit = 0
        net_profit = 0
        profit_of_unit = 0
        percent = 0
        if self.see_profit:
            net_cost_price = record['sub_total_price'] if record['sub_total_price']  else 0
            net_profit = net_price - net_cost_price
            if net_qty != 0:
                cost_price_unit = net_cost_price / net_qty
                profit_of_unit = net_profit / net_qty
            total_purchase_cost_row += (net_cost_price)
            total_standard_cost += cost_price_unit
            percent = net_profit * 100 / net_cost_price if net_cost_price > 0 else 1

            sheet.write(rowx, colx, net_cost_price, format_content_float)
            colx += 1
            sheet.write(rowx, colx, cost_price_unit , format_content_float)  # ББӨ
            sheet.write_comment(rowx, colx, 'Unit Cost Price: '+str(cost_price_unit))
            colx+=1
            sheet.write_formula(rowx, colx, '{='+alp_col_list[12+temp]+str(rowx+1)+'-'+alp_col_list[15+temp]+str(rowx+1)+'}', format_content_float if net_profit >= 0 else format_red_text) # Цэвэр ашиг net_profit
            colx+=1
            sheet.write_formula(rowx, colx, '{='+alp_col_list[17+temp]+str(rowx+1)+'/'+alp_col_list[11+temp]+str(rowx+1)+'}', format_content_float) #  Нэгжид ноогдох ашиг profit_of_unit
            colx+=1
            sheet.write_formula(rowx, colx, '{=('+alp_col_list[17+temp]+str(rowx+1)+'*100)/'+alp_col_list[15+temp]+str(rowx+1)+'}', format_content_float if percent >= 0 else format_red_text)  # Хувь percent
        before_value.update({'code': record['code'], 'name': record['product_name'], 'product_id': record['product_id']})
        if lot != 0:
            # Дан утга биш үед
            if not is_solo:
                sheet.merge_range(rowx - counter, 0, rowx - 1, 0, serial_seq, format_content_center)
                sheet.merge_range(rowx - counter, 1, rowx - 1, 1, before_value['code'], format_content_center)
                sheet.merge_range(rowx - counter, 2, rowx - 1, 2, before_value['name'] + '(' + str(counter) + ')', format_content_text)
            # Дан утга үед
            else:
                sheet.write(rowx - 1, 0, serial_seq, format_content_center)
                sheet.write(rowx - 1, 1, before_value['code'], format_content_center)
                sheet.write(rowx - 1, 2, before_value['name'], format_content_text)
        return sheet, sale_qty, sale_price, price, tax, sale_tax, price_tax, sale_price_tax, without_tax_discount, tax_discount, with_tax_discount, \
                        rev_qty, rev_price, rev_tax, rev_price_tax, net_qty,net_price, net_tax, net_price_tax, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent, \
                        total_qty, total_price, total_tax, total_price_tax, total_without_tax_discount, total_tax_discount, total_with_tax_discount, total_rev_qty, total_rev_price, total_rev_tax,total_rev_price_tax, net_total_qty, total_price_net,\
                        total_tax_net, total_price_tax_net, total_purchase_cost_row, total_standard_cost
                        
    def export_report(self):
        # create workbook
        output = BytesIO()
        book = xlsxwriter.Workbook(output)
        # НӨАТ төлдөг эсэх
        sale_tax_pay = False
        if not self.company_id.account_sale_tax_id:
            sale_tax_pay = True

        # create name
        report_name = _('Sales Report')
        file_name = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'),)
        # create formats
        format = self.get_format(book)
        # create report object
        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=('sales_report'), form_title=file_name).create({})
        # create sheet
        sheet, rowx = self.get_sheet(book, format, report_name)
        # Хэрэглэх хувьсагчид
        seq = 1
        lot = 0 if not self.see_serial else 1 if self.lot_ids else 2
        total_tax = total_price_tax = total_qty = total_without_tax_discount = total_tax_discount = total_with_tax_discount = total_price = rev_price = rev_qty = rev_tax = rev_price_tax = 0
        total_rev_qty = total_rev_price = total_rev_tax = total_rev_price_tax = total_purchase_cost_row = total_standard_cost = 0
        net_total_qty = total_price_net = total_tax_net = total_price_tax_net = 0

        check_ids = []
        check_warehouse_ids = []
        check_location_ids = []
        check_cat_ids = []
        check_brand_ids = []
        check_salesman_ids = []
        check_salesteam_ids = []
        check_customer_ids = []
        check_supplier_ids = []
        last_ware_rowx = last_location_rowx = last_cat_rowx = last_brand_rowx = last_salesman_rowx = last_salesteam_rowx = last_customer_rowx = last_supplier_rowx = -1
        warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum = self.get_dict()

        # Толгой хэсэг зурах
        sheet = self.get_header(sheet, rowx, format['format_title'], format['format_title_small'], lot, sale_tax_pay, True)
        rowx += 2
        # get data
        records = self.get_data()
        # Тайлан өрөлт
        temp = 1 if self.see_serial else 0
        for record in records:
            sub_cat = 0
            if self.group:
                check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                    warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum, \
                    last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx, \
                    rowx, sub_cat \
                    = self.stage_check('stage_one', self.stage_one, record,
                                       check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                                       warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum,
                                       sheet, lot, format['format_content_text_color'], format['format_sub_text_float'],
                                       last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx,
                                       rowx, sub_cat, sale_tax_pay)
                if self.stage_two:
                    check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                        warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum, \
                        last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx, \
                        rowx, sub_cat \
                        = self.stage_check('stage_two', self.stage_two, record,
                                           check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                                           warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum,
                                           sheet, lot, format['format_content_text_color'], format['format_sub_text_float'],
                                           last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx,
                                           rowx, sub_cat, sale_tax_pay)
                if self.stage_three:
                    check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids, \
                        warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum, \
                        last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx, \
                        rowx, sub_cat \
                        = self.stage_check('stage_three', self.stage_three, record,
                                           check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids,
                                           warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum,
                                           sheet, lot, format['format_content_text_color'], format['format_sub_text_float'],
                                           last_ware_rowx, last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx,
                                           rowx, sub_cat, sale_tax_pay)

            sheet, sale_qty, sale_price, price, tax, sale_tax, price_tax, sale_price_tax, without_tax_discount, tax_discount, with_tax_discount, \
                        rev_qty, rev_price, rev_tax, rev_price_tax, net_qty,net_price, net_tax, net_price_tax, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent, total_qty, total_price, total_tax, total_price_tax, total_without_tax_discount, total_tax_discount, total_with_tax_discount, total_rev_qty, total_rev_price, total_rev_tax,total_rev_price_tax, net_total_qty, total_price_net, total_tax_net, total_price_tax_net, total_purchase_cost_row, total_standard_cost = \
                        self.compute_data(sheet, rowx, seq, temp, record, format['format_content_center'], format['format_content_left'], format['format_content_text'], format['format_content_float'], format['format_red_text'], lot, sale_tax_pay, check_ids, sub_cat,total_qty, total_price, total_tax, total_price_tax, total_without_tax_discount, total_tax_discount, total_with_tax_discount, total_rev_qty, total_rev_price, total_rev_tax,total_rev_price_tax, net_total_qty, total_price_net, total_tax_net, total_price_tax_net, total_purchase_cost_row, total_standard_cost, True)
            rowx += 1
            seq += 1
            sheet = self.get_sum_dict(sheet, record, warehouse_sum, location_sum, cat_sum, brand_sum, salesman_sum, salesteam_sum, customer_sum, supplier_sum, sale_qty, sale_price, sale_tax, sale_price_tax, without_tax_discount, tax_discount, with_tax_discount, \
                        rev_qty, rev_price, rev_tax, rev_price_tax, net_qty, net_price, net_tax, net_price_tax, net_cost_price, cost_price_unit, net_profit, profit_of_unit, percent, last_ware_rowx, \
                        last_location_rowx, last_cat_rowx, last_brand_rowx, last_salesman_rowx, last_salesteam_rowx, last_customer_rowx, last_supplier_rowx, lot, sale_tax_pay, format['format_title'], format['format_sub_text_float'] )

            if self.group:
                check_ids, check_warehouse_ids, check_location_ids, check_cat_ids, check_brand_ids, check_salesman_ids, check_salesteam_ids, check_customer_ids, check_supplier_ids = self._get_append_sub_header(record)

        # Тайлангийн хөл дүнгүүдийг зурах
        sheet = self._get_footer_total_amount(sheet, rowx, format['format_title'], format['format_title_float'], total_qty, total_price, total_tax, total_price_tax, total_without_tax_discount, total_tax_discount, total_with_tax_discount, total_rev_qty, total_rev_price, total_rev_tax,\
                                total_rev_price_tax, net_total_qty, total_price_net, total_tax_net, total_price_tax_net, total_purchase_cost_row, total_standard_cost, lot, sale_tax_pay,True)
        rowx += 3
        # END OF THE REPORT

        # create footer
        sheet = self.get_footer(sheet, rowx, format)
        book.close()
        # set file data
        report_excel_output_obj.filedata = base64.b64encode(output.getvalue())
        # call export function
        return report_excel_output_obj.export_report()