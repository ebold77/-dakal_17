# -*- coding: utf-8 -*-
import base64
import logging
import time
from datetime import datetime, timedelta
from io import BytesIO

import pytz
import xlsxwriter
from lxml import etree
from odoo.addons.l10n_mn_web.models.time_helper import get_display_day_to_user_day, get_day_like_display

from odoo import _, api, fields, models
from odoo.addons.l10n_mn_report.tools.report_excel_cell_styles import ReportExcelCellStyles
from odoo.exceptions import UserError
from odoo.addons.l10n_mn_web.models.time_helper import *

_logger = logging.getLogger('stock.report')


class ProductMoveCheckReportWizard(models.TransientModel):
    _name = 'product.move.check.report.wizard'
    _description = 'Product Move Check Wizard'

    def _default_product(self):
        context = self._context or {}
        if 'active_id' in context and context['active_id']:
            return context['active_id']
        return False

    def _default_report_type(self):
        if self.env.user.has_group('account.group_account_user'):
            res = 'price'
        else:
            res = 'owner'
        return res

    def _default_warehouse(self):
        res = 0
        if self.env.user and self.env.user.allowed_warehouse_ids:
            res = self.env.user.allowed_warehouse_ids[0].id
        return res

    def _default_level(self):
        if self.env.user.has_group('account.group_account_user'):
            level = 'manager'
        else:
            level = 'owner'
        return level

    def get_report_type(self):
        res = [('owner', _('QTY')),
               ('price', _('List Price'))]
        if self.env.user.has_group('l10n_mn_stock.group_stock_view_cost'):
            res.append(('cost', _('Cost Price')))
        return res

    @api.depends("product_ids")
    def compute_product_id(self):
        if self.product_ids:
            self.product_id = self.product_ids[0]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductMoveCheckReportWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            if 'warehouse_id' in res['fields']:
                res['fields']['warehouse_id']['domain'] = [
                    ('id', 'in', self.env.user.allowed_warehouse_ids.ids)]
        return res

    report_type = fields.Selection(get_report_type, 'Report Type', default=_default_report_type, required=True)
    level = fields.Selection([('owner', 'Owner'),
                              ('manager', 'Manager')], 'Level', default=_default_level, required=True)
    from_date = fields.Date('From Date', default=fields.Date.context_today, required=True)
    to_date = fields.Date('To Date', default=fields.Date.context_today, required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_default_warehouse, required=True)
    product_id = fields.Many2one('product.product', 'Product', default=_default_product, compute="compute_product_id",
                                 required=True)
    category_id = fields.Many2one('product.category', 'Category')
    prodlot_id = fields.Many2one('stock.production.lot', 'Production Lot')
    save = fields.Boolean('Save to document storage')
    draft = fields.Boolean('Draft View')
    product_ids = fields.Many2many('product.product', string="Products")

    @api.onchange('category_id')
    def categ_id_change(self):
        res = {}
        if self.category_id:
            self.env.cr.execute(""" SELECT p.id FROM product_template p
                                        WHERE categ_id = %s""" % (self.category_id.id,))
            templ_ids = [p['id'] for p in self.env.cr.dictfetchall()]
            return ({'domain': {'product_id': [('product_tmpl_id', 'in', templ_ids)]}})
        else:
            return res

    @api.onchange('prodlot_id')
    def prodlot_id_change(self):
        res = {}
        if self.prodlot_id:
            self.env.cr.execute(
                """SELECT p.id FROM stock_production_lot p WHERE product_id = %s""" % (self.prodlot_id.id))
            prodlot_ids = [p['id'] for p in self.env.cr.dictfetchall()]
            return ({'domain': {'prodlot_id': [('id', 'in', prodlot_ids)]}})
        else:
            return res

    def get_log_message(self, product):
        return _('Product move check report (Warehouse ="%s", Product = "%s", Start date = "%s", End date = "%s")') % (
        self.warehouse_id.name, product.name, self.from_date, self.to_date)

    def get_available(self, wiz):
        ''' Эхний үлдэгдэл тооцож байна '''
        qty = 0
        from_date = str(wiz['from_date']) + ' 23:59:59'
        fdate = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
        fdate = get_display_day_to_user_day(fdate, self.env.user)
        self.env.cr.execute("SELECT view_location_id FROM stock_warehouse WHERE id = %s" % wiz['warehouse_id'])
        res2 = self.env.cr.dictfetchall()
        if res2:
            location_ids = self.env['stock.location'].search(
                [('location_id', 'child_of', [res2[0]['view_location_id']]), ('usage', '=', 'internal')])
            if location_ids:
                self._cr.execute("SELECT  "
                                 "sum(a.product_qty) AS quantity "
                                 "FROM ( "
                                 "SELECT "
                                 "sm.product_id, "
                                 "sm.product_qty / uom.factor * uom2.factor as product_qty, "
                                 "sm.date "
                                 "FROM "
                                 "stock_move sm "
                                 " LEFT JOIN product_product AS pp ON sm.product_id = pp.id "
                                 " LEFT JOIN product_template AS pt ON pp.product_tmpl_id = pt.id "
                                 " LEFT JOIN uom_uom AS uom ON sm.product_uom = uom.id "
                                 " LEFT JOIN uom_uom AS uom2 ON pt.uom_id = uom2.id "
                                 "WHERE "
                                 "sm.date <= %s "
                                 "AND sm.product_id = %s "
                                 "AND sm.location_dest_id IN (" + str(location_ids.ids)[1:-1] + ") "
                                 "AND sm.location_id NOT IN (" + str(location_ids.ids)[1:-1] + ") "
                                 "AND sm.state = 'done' "
                                 "UNION ALL "
                                 "SELECT "
                                 "sm.product_id, "
                                 "- sm.product_qty / uom.factor * uom2.factor as product_qty, "
                                 "sm.date "
                                 "FROM "
                                 "stock_move sm "
                                 " LEFT JOIN product_product AS pp ON sm.product_id = pp.id "
                                 " LEFT JOIN product_template AS pt ON pp.product_tmpl_id = pt.id "
                                 " LEFT JOIN uom_uom AS uom ON sm.product_uom = uom.id "
                                 " LEFT JOIN uom_uom AS uom2 ON pt.uom_id = uom2.id "
                                 "WHERE "
                                 "sm.date <= %s "
                                 "AND sm.product_id = %s "
                                 "AND sm.location_dest_id NOT IN (" + str(location_ids.ids)[1:-1] + ") "
                                 "AND sm.location_id IN (" + str(location_ids.ids)[1:-1] + ")"
                                 "AND sm.state = 'done') AS a ",
                                 (str(fdate), wiz['prod_id'], str(fdate), wiz['prod_id']))
                stock = self.env.cr.dictfetchall()
                if stock and stock[0] and stock[0]['quantity']:
                    qty = stock[0]['quantity']
                return qty
        return 0

    def get_first_cost(self, wiz):
        ''' Тухайн барааны эхний хугацаандах өртөгүүдийг олно.'''
        res = 0.0
        where = where_not = ''
        prod_id = wiz['prod_id']
        wid = wiz['warehouse_id']
        self.env.cr.execute('select view_location_id from stock_warehouse where id=%s', (wid,))
        res2 = self.env.cr.dictfetchall()
        location_ids = self.env['stock.location'].search(
            [('location_id', 'child_of', [res2[0]['view_location_id']]), ('usage', '=', 'internal')])
        if location_ids:
            where = " AND m.location_id NOT IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')' + " AND m.location_dest_id IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')'
            where_not = " AND m.location_id IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')' + " AND m.location_dest_id NOT IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')'
        from_date = str(wiz['from_date']) + ' 23:59:59'
        fdate = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
        fdate = get_display_day_to_user_day(fdate, self.env.user)
        self.env.cr.execute("""SELECT (m.price_unit * uom.factor / uom2.factor) AS cost,m.date AS date,
                        (m.product_qty / uom.factor * uom2.factor) AS in_qty,
                        (select 0) AS out_qty
                        FROM stock_move AS m
                          LEFT JOIN stock_picking AS p ON m.picking_id = p.id
                          LEFT JOIN res_partner AS rp ON p.partner_id = rp.id
                          LEFT JOIN product_product AS pp ON m.product_id = pp.id
                          LEFT JOIN product_template AS pt ON pp.product_tmpl_id = pt.id
                          LEFT JOIN uom_uom AS uom ON m.product_uom = uom.id
                          LEFT JOIN uom_uom AS uom2 ON pt.uom_id = uom2.id
                        WHERE m.product_id = %s
                          AND m.state = 'done'
                          AND m.product_qty is not null
                          AND m.date <= %s """ + where + """
                    UNION ALL
                    SELECT (m.price_unit * uom.factor / uom2.factor) AS cost, m.date AS date,
                        (select 0) AS in_qty,
                        (m.product_qty / uom.factor * uom2.factor) AS out_qty
                        FROM stock_move AS m
                            LEFT JOIN stock_picking AS p ON m.picking_id = p.id
                            LEFT JOIN res_partner AS rp ON p.partner_id = rp.id
                            LEFT JOIN product_product AS pp ON m.product_id = pp.id
                            LEFT JOIN product_template AS pt ON pp.product_tmpl_id = pt.id
                            LEFT JOIN uom_uom AS uom ON m.product_uom = uom.id
                            LEFT JOIN uom_uom AS uom2 ON pt.uom_id = uom2.id
                        WHERE m.product_id = %s
                          AND m.state = 'done'
                          AND m.product_qty is not null
                          AND m.date <= %s """ + where_not + """
                    ORDER BY date
                    """, (prod_id, fdate, prod_id, fdate,))
        stock = self.env.cr.dictfetchall()
        if stock:
            tmp_cost = 0.0
            qty = 0
            for st in stock:
                if st['in_qty'] > 0:
                    qty += st['in_qty']
                if st['out_qty'] > 0:
                    qty -= st['out_qty']
                tmp_cost = st['cost']
            res = tmp_cost
        return res

    def get_price(self, wiz, ptype):
        # Үнийн түүхээс аль үнийн түүхийг сонгож авахыг асуух
        price = 0.0
        context = self._context or {}
        from_date = str(wiz['from_date']) + ' 23:59:59'
        fdate = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') - timedelta(days=1)
        fdate = get_display_day_to_user_day(fdate, self.env.user)
        if ptype == 'first':
            self.env.cr.execute("select h.list_price from product_price_history h "
                                "join product_template t on (h.product_template_id = t.id) "
                                "join product_product p on (t.id = p.product_tmpl_id) "
                                "where p.id = %s and h.datetime <= %s "
                                "and h.company_id = %s "
                                "order by h.datetime desc limit 1",
                                (wiz['prod_id'], fdate, wiz['company_id']))  # and h.price_type = wiz['price_type']
            fetched = self.env.cr.dictfetchall()
            if fetched and fetched[0]:
                price = fetched[0]['list_price']

        else:
            price = self.env['product.product'].browse(wiz['prod_id']).price_get('list_price')[wiz['prod_id']]
            self.env.cr.execute("select h.list_price from product_price_history h "
                                "join product_template t on (h.product_template_id = t.id) "
                                "join product_product p on (t.id = p.product_tmpl_id) "
                                "where p.id = %s and h.datetime <= %s "
                                "and h.company_id = %s "
                                "order by h.datetime desc limit 1", (wiz['prod_id'], str(wiz['to_date']) + ' 23:59:59',
                                                                     wiz['company_id']))  # and h.price_type = wiz['price_type']
            fetched = self.env.cr.dictfetchall()
            if fetched and fetched[0]:
                price = fetched[0]['list_price']
        return price

    def get_move_data(self, wiz):
        # тухайн барааны хөдөлгөөний тоо, байрлал, үнэ зэрэг мэдээллийн барааны хөдөлгөөнөөс шүүх
        res = []
        context = self._context or {}
        where = where_location = where_not_location = ''
        return_ids = []
        prod_id = wiz['prod_id']
        from_date = get_display_day_to_user_day('%s 00:00:00' % str(wiz['from_date']), self.env.user)
        to_date = get_display_day_to_user_day('%s 23:59:59' % str(wiz['to_date']), self.env.user)
        wid = wiz['warehouse_id']
        company = wiz['company_id']
        select_in = ''
        select_out = ''
        join = ''
        number_query = ''
        group_by = ''
        if 'sale.order' not in self.env or 'sale.category' not in self.env:
            raise UserError(_('Install Mongolian Sale module!'))
        if 'purchase.order' not in self.env:
            raise UserError(_('Install Purchase Management module!'))
        if 'mrp.production' in self.env:
            select_in = " WHEN m.production_id is not null THEN 'FP income' WHEN m.raw_material_production_id is not null THEN 'RM expense' "
            select_out = " WHEN m.production_id is not null THEN 'FP income' WHEN m.raw_material_production_id is not null THEN 'RM expense' "
            number_query = " WHEN m.production_id is not null THEN mrp.name "
            join = ' LEFT JOIN mrp_production AS mrp ON (m.production_id = mrp.id OR m.raw_material_production_id = mrp.id) '
            group_by = 'm.production_id, mrp.name,'
        if wiz['draft']:
            where += " AND m.state <> 'cancel' "
        else:
            where += " AND m.state = 'done' "
        select = """ SUM(coalesce(m.product_qty / u.factor * u2.factor)) AS qty"""
        self.env.cr.execute('select view_location_id from stock_warehouse where id=%s', (wiz['warehouse_id'],))
        res2 = self.env.cr.dictfetchall()
        location_ids = self.env['stock.location'].search(
            [('location_id', 'child_of', [res2[0]['view_location_id']]), ('usage', '=', 'internal')])
        if location_ids:
            where_location = "AND m.location_id IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')' + " AND m.location_dest_id NOT IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')'
            where_not_location = "AND m.location_id NOT IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')' + " AND m.location_dest_id IN " + '(' + ','.join(
                map(str, location_ids.ids)) + ')'
        self.env.cr.execute("""SELECT (CASE WHEN m.picking_id is not null THEN m.picking_id ELSE 0 END) AS picking, 
        m.date AS date, ('out') AS type,
                        (CASE WHEN m.picking_id is not null THEN rp.name WHEN m.warehouse_id is not null
                            and sw.partner_id is not null THEN rp2.name ELSE '' END) AS partner,
                        (CASE WHEN m.inventory_id is not null THEN 'inventory'  """ + select_out + """
                            ELSE '' END) AS rep_type, m.state AS state,
                        (CASE WHEN m.picking_id is not null THEN p.name
                            WHEN m.inventory_id is not null THEN i.name ELSE COALESCE(m.origin, 'pos') END) AS number,
                        SUM(DISTINCT coalesce(m.price_unit)) AS cost,
                        (pt.list_price) AS price, sl.name AS location,
                        m.origin AS origin,
                        """ + select + """

                    FROM stock_move AS m
                        LEFT JOIN stock_picking AS p ON (m.picking_id = p.id)
                        LEFT JOIN stock_picking_type AS spt ON (p.picking_type_id = spt.id)
                        LEFT JOIN res_partner AS rp ON (p.partner_id = rp.id)
                        """ + join + """
                        LEFT JOIN stock_inventory AS i ON (m.inventory_id = i.id)
                        JOIN product_product AS pp ON (m.product_id = pp.id)
                        JOIN product_template AS pt ON (pp.product_tmpl_id = pt.id)
                        JOIN uom_uom AS u ON (m.product_uom = u.id)
                        JOIN uom_uom AS u2 ON (pt.uom_id = u2.id)
                        JOIN stock_location AS sl ON (m.location_dest_id = sl.id)
                        LEFT JOIN stock_warehouse AS sw ON (m.warehouse_id = sw.id)
                        LEFT JOIN res_partner AS rp2 ON (sw.partner_id = rp2.id)
                    WHERE m.product_id = %s AND m.product_qty is not null
                        AND m.date >=%s AND m.date <= %s  """ + where + """ """ + where_location + """
                    GROUP BY m.id, m.date, m.picking_id, rp.name, pt.list_price, sl.name, m.warehouse_id, m.origin,
                    sw.partner_id, rp2.name, """ + group_by + """ m.state, m.inventory_id, sl.usage, p.picking_type_id, spt.code, p.name,
                    i.name
                UNION ALL
                    SELECT (CASE WHEN m.picking_id is not null THEN m.picking_id ELSE 0 END) AS picking, m.date AS date, ('in') AS type,
                        (CASE WHEN m.picking_id is not null THEN rp.name WHEN m.warehouse_id is not null
                            and sw.partner_id is not null THEN rp2.name ELSE '' END) AS partner,
                        (CASE WHEN m.inventory_id is not null THEN 'inventory' """ + select_in + """
                            ELSE '' END) AS rep_type, m.state AS state,
                        (CASE WHEN m.picking_id is not null THEN p.name
                        """ + number_query + """
                            WHEN m.inventory_id is not null THEN i.name ELSE COALESCE(m.origin, 'pos') END) AS number,
                            SUM(DISTINCT coalesce(m.price_unit)) AS cost,
                            pt.list_price AS price, sl.name AS location,
                        m.origin AS origin,
                        """ + select + """
                    FROM stock_move AS m
                        LEFT JOIN stock_picking AS p ON (m.picking_id = p.id)
                        LEFT JOIN stock_picking_type AS spt ON (p.picking_type_id = spt.id)
                        """ + join + """
                        LEFT JOIN res_partner AS rp ON (p.partner_id = rp.id)
                        LEFT JOIN stock_inventory AS i ON (m.inventory_id = i.id)
                        JOIN product_product AS pp ON (m.product_id = pp.id)
                        JOIN product_template AS pt ON (pp.product_tmpl_id = pt.id)
                        JOIN uom_uom AS u ON (m.product_uom = u.id)
                        JOIN uom_uom AS u2 ON (pt.uom_id = u2.id)
                        JOIN stock_location AS sl ON (m.location_id = sl.id)
                        LEFT JOIN stock_warehouse AS sw ON (m.warehouse_id = sw.id)
                        LEFT JOIN res_partner AS rp2 ON (sw.partner_id = rp2.id)
                    WHERE m.product_id = %s AND m.product_qty is not null
                        AND m.date >= %s  AND m.date <= %s """ + where + """ """ + where_not_location + """
                    GROUP BY m.id, m.date, m.picking_id, rp.name, m.warehouse_id, sw.partner_id, rp2.name, p.name, m.inventory_id, i.name, m.state, m.origin,
                    """ + group_by + """ sl.usage, p.picking_type_id, spt.code, pt.list_price, sl.name
                ORDER BY date, type""", (prod_id, from_date, to_date, prod_id, from_date, to_date))
        result = self.env.cr.dictfetchall()
        for r in result:
            in_qty = out_qty = in_lot_qty = out_lot_qty = 0.0
            if r['type'] == 'in':
                in_qty = r['qty']
            else:
                out_qty = r['qty']
            date = datetime.strptime(str(r['date']).split(".")[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            if wiz['report_type'] != 'price' and r['type'] == 'price':
                continue
            res.append({'date': date,
                        'state': r['state'],
                        'location': r['location'],
                        'number': r['number'],
                        'rep_type': r['rep_type'],
                        'origin': r['origin'] if 'origin' in r.keys() else '',
                        'partner': r['partner'],
                        'price': r['price'],
                        'in_qty': in_qty,
                        'out_qty': out_qty,
                        'in_lot_qty': in_lot_qty,
                        'out_lot_qty': out_lot_qty,
                        'picking': r['picking'],
                        'cost': r['cost'] or 0.0
                        })
        return res

    def print_report(self):
        # pdf файл хэвлэх процесс
        context = self._context or {}
        user = self.env.user
        wiz = {}
        wiz.update({'company_id': user.company_id.id})
        lot_name = ''
        due_date = ''
        if self.prodlot_id:
            lot = self.prodlot_id
            if lot and lot.name:
                lot_name = lot.name
            if lot and lot.expiration_date:
                due_date = lot.expiration_date
        wiz.update({'draft': self.draft,
                    'report_type': self.report_type,
                    'warehouse_id': self.warehouse_id.id,
                    'wname': self.warehouse_id.name,
                    'prod_id': self.product_id.id,
                    'from_date': self.from_date,
                    'to_date': self.to_date})
        wiz.update({'report_type': self.report_type})
        wiz.update({'warehouse_id': self.warehouse_id.id})
        wiz.update({'prod_id': self.product_id.id})
        wiz.update({'lot_id': (self.prodlot_id and self.prodlot_id.id) or False})
        first_avail = self.get_available(wiz)
        first_cost = self.get_first_cost(wiz) or 0
        first_price = self.get_price(wiz, 'first')
        result = self.get_move_data(wiz)
        data = {
            'ids': [],
            'model': 'product.move.check.report.wizard',
            'self': self,
            'wizard': {'from_date': self.from_date,
                       'to_date': self.to_date,
                       'prod_id': self.product_id.id,
                       'company': user.company_id.name,
                       'company_id': user.company_id.id,
                       'lot_name': lot_name,
                       'expiration_date': due_date,
                       'warehouse_id': self.warehouse_id.id,
                       'wname': self.warehouse_id.name,
                       'report_type': self.report_type,
                       'first_avail': first_avail,
                       'first_cost': first_cost,
                       'first_price': first_price,
                       'draft': self.draft,
                       'prodlot_id': self.prodlot_id.id}
        }
        if data['self'].report_type == 'owner':
            body = (
                       _('Product move check report (Start date="%s", End date="%s", Product="%s",Warehouse="%s",prodlot_id="%s"')
                       ) % (self.from_date, self.to_date, self.product_id.name, self.warehouse_id.name,
                            self.prodlot_id and self.prodlot_id.name)
            message = _('[Report][PDF][PROCESSING] %s') % body
            _logger.info(message)
        elif data['self'].report_type == 'price':
            body = (
                       _('Product move check report (Price Unit)(Start date="%s", End date="%s", Product="%s",Warehouse="%s",prodlot_id="%s"')
                       ) % (self.from_date, self.to_date, self.product_id.name, self.warehouse_id.name,
                            self.prodlot_id and self.prodlot_id.name)
            message = _('[Report][PDF][PROCESSING] %s') % body
            _logger.info(message)
        elif data['self'].report_type == 'cost':
            body = (
                       _('Product move check report (Cost)(Start date="%s", End date="%s", Product="%s",Warehouse="%s",prodlot_id="%s"')
                       ) % (self.from_date, self.to_date, self.product_id.name, self.warehouse_id.name,
                            self.prodlot_id and self.prodlot_id.name)
            message = _('[Report][PDF][PROCESSING] %s') % body
            _logger.info(message)
        data.update({'self': self.id})
        return self.env.ref('l10n_mn_stock_report.product_move_check_report_report').report_action(None, data=data)

    def export_report(self):
        # Тайлан хэвлэх процесс
        output = BytesIO()
        book = xlsxwriter.Workbook(output)
        report_name = self._name.replace('.', '_')
        filename = "%s_%s.xls" % (report_name, time.strftime('%Y%m%d_%H%M'))

        format_title = book.add_format(ReportExcelCellStyles.format_title)
        # Баримтын толгой
        format_filter = book.add_format(ReportExcelCellStyles.format_filter)
        # Хүснэгтийн толгой
        format_group = book.add_format(ReportExcelCellStyles.format_group)
        format_group_float = book.add_format(ReportExcelCellStyles.format_group_float)
        format_group_left = book.add_format(ReportExcelCellStyles.format_group_left)
        format_content_bold_float = book.add_format(ReportExcelCellStyles.format_content_bold_float)
        format_content_bold_float_color = book.add_format(ReportExcelCellStyles.format_content_bold_float_color)
        # Хүснэгтийн агуулга
        format_content_bold_text = book.add_format(ReportExcelCellStyles.format_content_bold_text)
        format_content_center = book.add_format(ReportExcelCellStyles.format_content_center)
        format_content_float = book.add_format(ReportExcelCellStyles.format_content_float)
        format_content_float_color = book.add_format(ReportExcelCellStyles.format_content_float_color)
        format_content_center_color = book.add_format(ReportExcelCellStyles.format_content_center_color)
        report_excel_output_obj = self.env['oderp.report.excel.output'].with_context(filename_prefix=(report_name),
                                                                                     self_title=filename).create({})

        sheet = book.add_worksheet(report_name)
        sheet.set_landscape()
        sheet.set_paper(9)  # A4
        sheet.set_margins(0.78, 0.39, 0.39, 0.39)  # 2cm, 1cm, 1cm, 1cm
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&C&"Arial"&9&P', {'margin': 0.1})
        rowx = 0

        module = self.sudo().env['ir.module.module'].search([('name', '=', 'l10n_mn_product_expense')])
        user = self.env.user
        report_name = u''
        mayagt = u''
        if self.report_type == 'price':
            mayagt = _('FORM PT-5-3')
            report_name = _('Product move check report (Price Unit)')
        elif self.report_type == 'cost':
            mayagt = _('FORM PT-5-2')
            report_name = _('Product move check report (Cost)')
        else:
            mayagt = _('FORM PT-5-1')
            report_name = _('Product move check report')
        sheet.write(rowx, 0, user.company_id.partner_id.name, format_filter)
        sheet.write(rowx, 9, mayagt, format_filter)
        rowx += 2
        sheet.merge_range(rowx, 0, rowx, 9, report_name, format_title)
        now_date = str(get_day_like_display(fields.Datetime.now(), user))[:16]
        rowx += 2
        sheet.write(rowx, 1, _('Sector name: %s') % (self.warehouse_id.name), format_filter)
        sheet.write(rowx, 5, _('Check Duration: %s - %s') % (self.from_date, self.to_date), format_filter)
        sheet.write(rowx + 1, 1, _('Printed Date: %s') % (now_date), format_filter)
        rowx += 3
        count = 0
        inch = 300

        sheet.merge_range(rowx, 0, rowx + 1, 0, _('Seq'), format_group)
        sheet.merge_range(rowx, 1, rowx, 5, _('Document'), format_group)
        sheet.write(rowx + 1, 1, _('Date'), format_group)
        sheet.write(rowx + 1, 2, _('Type'), format_group)
        sheet.write(rowx + 1, 3, _('Number'), format_group)
        sheet.write(rowx + 1, 4, _('Move'), format_group)
        sheet.write(rowx + 1, 5, _('Serial'), format_group)
        sheet.merge_range(rowx, 6, rowx + 1, 6, _('Partner'), format_group)
        if self.report_type == 'owner':
            sheet.merge_range(rowx, 7, rowx, 9, _('QTY'), format_group)
            sheet.write(rowx + 1, 7, _('Income'), format_group)
            sheet.write(rowx + 1, 8, _('Expense'), format_group)
            sheet.write(rowx + 1, 9, _('Balance'), format_group)
        elif self.report_type == 'price':
            sheet.merge_range(rowx, 7, rowx + 1, 7, _("QTY"), format_group)
            sheet.merge_range(rowx, 8, rowx, 10, _('Total /MNT/'), format_group)
            sheet.write(rowx + 1, 8, _('Income'), format_group)
            sheet.write(rowx + 1, 9, _('Expense'), format_group)
            sheet.write(rowx + 1, 10, _('Balance'), format_group)
            sheet.merge_range(rowx, 11, rowx + 1, 11, _("Balance Quantity"), format_group)
        else:
            sheet.merge_range(rowx, 7, rowx + 1, 7, _("QTY"), format_group)
            sheet.merge_range(rowx, 8, rowx, 10, _('Total /Cost/'), format_group)
            sheet.write(rowx + 1, 8, _('Income'), format_group)
            sheet.write(rowx + 1, 9, _('Expense'), format_group)
            sheet.write(rowx + 1, 10, _('Balance'), format_group)
            sheet.merge_range(rowx, 11, rowx + 1, 11, _("Balance Quantity"), format_group)
        rowx += 2
        for product in self.product_ids:
            body = self.get_log_message(product)
            message = _('[Product move check report][XLS][PROCESSING] %s') % body
            _logger.info(message)

            wiz = {}
            ctx = self._context.copy()
            if 'company' not in ctx:
                ctx.update({'company_id': user.company_id.id})
            wiz.update({'company_id': user.company_id.id})
            lot_name = due_date = '..................'
            max_qty = min_qty = '..................'
            wiz['draft'] = self.draft
            wiz.update({'draft': self.draft,
                        'report_type': self.report_type,
                        'warehouse_id': self.warehouse_id.id,
                        'prod_id': product.id,
                        'from_date': self.from_date,
                        'to_date': self.to_date})
            wiz.update({'lot_id': (self.prodlot_id and self.prodlot_id.id) or False})
            if self.prodlot_id:
                lot = self.prodlot_id
                if lot and lot.name:
                    lot_name = lot.name
                if lot and lot.expiration_date:
                    due_date = lot.expiration_date

            first_avail = self.get_available(wiz) or 0
            first_avail_lot = first_avail
            result = self.get_move_data(wiz)
            self.env.cr.execute("""SELECT product_max_qty AS max_qty, product_min_qty AS min_qty
                          FROM stock_warehouse_orderpoint WHERE product_id = %s AND warehouse_id = %s""" % (
            product.id, self.warehouse_id.id))
            point = self.env.cr.dictfetchall()
            if point and point[0]['max_qty']:
                max_qty = str(point[0]['max_qty'])
            if point and point[0]['min_qty']:
                min_qty = str(point[0]['min_qty'])
            sheet.write(rowx, 0, "", format_group)
            prod_info = ""
            if product.default_code:
                prod_info += (str(product.default_code) + " ")
            if product.barcode:
                prod_info += (str(product.barcode) + " ")
            if product.name:
                prod_info += str(product.name)
            prod_info = prod_info.strip()
            sheet.write(rowx, 1, prod_info, format_group_left)
            sheet.write(rowx, 2, "", format_group)
            sheet.write(rowx, 3, "", format_group)
            resources = _("Safety Stock: %s") % (min_qty) + " " + _("Max Stock: %s") % (max_qty)
            sheet.write(rowx, 4, resources, format_group_left)
            sheet.write(rowx, 5, "", format_group)
            sheet.write(rowx, 6, _('Initial Balance'), format_group)
            if self.report_type == 'owner':
                sheet.write(rowx, 7, _('X'), format_group)
                sheet.write(rowx, 8, _('X'), format_group)
                sheet.write(rowx, 9, first_avail, format_content_bold_float_color)
            elif self.report_type == 'price':
                first_price = self.get_price(wiz, 'first') or 0
                change = change_total = change_total_lot = 0
                if first_price != 0:
                    change = first_price
                sheet.write(rowx, 7, first_avail, format_content_bold_float_color)
                sheet.write(rowx, 8, u'X', format_group)
                sheet.write(rowx, 9, u'X', format_group)
                sheet.write(rowx, 10, (first_avail != 0 and first_price != 0) and (first_avail * first_price) or '',
                            format_group)
                sheet.write(rowx, 11, first_avail, format_content_bold_float_color)
            else:
                first_cost = self.get_first_cost(wiz) or 0
                last_cost = first_cost or 0
                balance = (first_avail * first_cost) or 0
                lot_balance = (first_avail * first_cost) or 0
                sheet.write(rowx, 7, first_avail, format_content_bold_float_color)
                sheet.write(rowx, 8, u'X', format_group)
                sheet.write(rowx, 9, u'X', format_group)
                sheet.write(rowx, 10, (first_avail != 0 and first_cost != 0) and (first_avail * first_cost) or "0.0",
                            format_content_bold_float_color)
                sheet.write(rowx, 11, first_avail, format_content_bold_float_color)
            rowx += 1

            in_total = out_total = in_lot_total = out_lot_total = 0
            qty = unit = 0

            seri = ''
            if result:
                for r in result:
                    price = 0  # self.product_id.lst_price
                    diff = 0
                    count += 1
                    rep_type = ''
                    number = partner = seri = supply_warehouse_name = ''
                    in_qty = out_qty = in_lot_qty = out_lot_qty = 0
                    if r['number']:
                        if r['number'] == 'pos':
                            number = r['location']
                        elif self.report_type == 'price' and r['number'] == 'price':
                            if r['price']:
                                change = r['price']
                            number = _('Price diff')
                        else:
                            number = r['number']
                    if r['partner']:
                        partner = r['partner']
                    if r['in_qty'] and r['in_qty'] != 0:  # Орлого тооцох хэсэг
                        qty += r['in_qty']
                        in_qty = r['in_qty']
                        first_avail += r['in_qty'] or 0
                        diff = r['in_qty']
                        if self.report_type == 'owner':
                            in_total += r['in_qty']
                        elif self.report_type == 'price' and r['price']:
                            in_total += (in_qty * r['price'])
                        elif self.report_type == 'cost' and r['cost']:
                            in_total += (in_qty * r['cost'])
                            balance += (in_qty * r['cost'])
                        if self.report_type == 'cost' and first_avail != 0:
                            last_cost = balance / first_avail
                    if r['in_lot_qty'] and r['in_lot_qty'] != 0:  # Цувралтай бол цувралын орлого тооцох хэсэг
                        qty += r['in_qty']
                        in_lot_qty = r['in_lot_qty']
                        first_avail_lot += r['in_lot_qty'] or 0
                        diff = r['in_lot_qty']
                        if self.report_type == 'owner':
                            in_total += r['in_qty']
                        elif self.report_type == 'price' and r['price']:
                            in_lot_total += (in_lot_qty * r['price'])
                        elif self.report_type == 'cost' and r['cost']:
                            in_lot_total += (in_lot_qty * r['cost'])
                            lot_balance += (in_lot_qty * r['cost'])
                        if self.report_type == 'cost' and first_avail_lot != 0:
                            last_cost = lot_balance / first_avail_lot
                    if r['out_qty'] and r['out_qty'] != 0:  # Зарлага тооцох хэсэг
                        qty += r['out_qty']
                        out_qty = r['out_qty']
                        first_avail -= r['out_qty'] or 0
                        diff = r['out_qty']
                        if self.report_type == 'owner':
                            out_total += r['out_qty']
                        elif self.report_type == 'price' and r['price']:
                            out_total += (out_qty * r['price'])
                        elif self.report_type == 'cost' and r['cost']:
                            out_total += (out_qty * r['cost'])
                            balance -= (out_qty * r['cost'])
                            last_cost = r['cost']
                    if r['out_lot_qty'] and r['out_lot_qty'] != 0:  # Цувралтай бол цувралын зарлага тооцох хэсэг
                        qty += r['out_qty']
                        out_lot_qty = r['out_lot_qty']
                        first_avail_lot -= r['out_lot_qty'] or 0
                        diff = r['out_lot_qty']
                        if self.report_type == 'owner':
                            out_total += r['out_qty']
                        elif self.report_type == 'price' and r['price']:
                            out_lot_total += (out_lot_qty * r['price'])
                        elif self.report_type == 'cost' and r['cost']:
                            out_lot_total += (out_lot_qty * r['cost'])
                            lot_balance -= (out_lot_qty * r['cost'])
                            last_cost = r['cost']
                    if self.report_type == 'price' and r['price']:
                        if change == 0:
                            change = r['price']
                        if change != r['price']:
                            if r['number'] and r['number'] == 'price':
                                unit = (r['price'] - change)
                                change_total += (unit * first_avail)
                                change_total_lot += (unit * first_avail_lot)
                        price = r['price']
                    cost = 0.0
                    if self.report_type == 'cost' and r['cost']:
                        cost = r['cost']

                    picking_id = 0
                    if r['picking']:
                        picking_id = r['picking']
                    if picking_id > 0:
                        picking = self.env['stock.picking'].search([('id', '=', picking_id)])
                        if picking.transit_order_id:
                            rep_type = _('Transit')
                            supply_warehouse_name += picking.transit_order_id.supply_warehouse_id.name + ' --> ' + picking.transit_order_id.warehouse_id.name
                        elif 'product.expense' in self.env and picking.expense_id:
                            supply_warehouse_name = picking.expense_id.code or ''
                        elif 'technic.expense.fuel' in self.env and picking.fuel_expense_id:
                            supply_warehouse_name = picking.fuel_expense_id.name or ''
                        if module.state == 'installed' and picking.expense_id:
                            rep_type = _('Expense')
                        elif picking.picking_type_id.code == 'internal':
                            rep_type = _('Internal Move')
                        elif picking.group_id:
                            sale = self.env['sale.order'].search([('procurement_group_id', '=', picking.group_id.id)])
                            if sale:
                                rep_type = _('Sales / (%s)') % sale.sale_category_id.name or ''
                        for line in picking.move_lines:
                            if line.purchase_line_id:
                                rep_type = _('Purchase')
                            elif line.origin_returned_move_id:
                                rep_type = _('Return')
                    if r['rep_type']:
                        if r['rep_type'] == 'inventory':
                            rep_type = _('Inventory')
                        else:
                            rep_type = r['rep_type']
                    if rep_type == '':
                        rep_type = _('Point of Sale')

                    if self.draft and r['state'] != 'done':
                        content = format_content_center_color
                        content_float = format_content_float_color
                    else:
                        content = format_content_center
                        content_float = format_content_float

                    date_format = str(get_day_like_display(r['date'], self.env.user))

                    sheet.write(rowx, 0, count, content)
                    sheet.write(rowx, 1, date_format, content)
                    sheet.write(rowx, 2, rep_type, content)
                    sheet.write(rowx, 3, number, content)
                    sheet.write(rowx, 4, supply_warehouse_name, content)
                    sheet.write(rowx, 5, seri, content)
                    sheet.write(rowx, 6, partner, content)
                    if self.report_type == 'owner':
                        if seri:
                            sheet.write(rowx, 7, (in_lot_qty != 0 and in_lot_qty) or '', content_float)
                            sheet.write(rowx, 8, (out_lot_qty != 0 and out_lot_qty) or '', content_float)
                            sheet.write(rowx, 9, first_avail_lot, content_float)
                        else:
                            sheet.write(rowx, 7, (in_qty != 0 and in_qty) or '', content_float)
                            sheet.write(rowx, 8, (out_qty != 0 and out_qty) or '', content_float)
                            sheet.write(rowx, 9, first_avail, content_float)
                    elif self.report_type == 'price':
                        sheet.write(rowx, 7, (diff != 0 and diff) or "", content_float)
                        if seri:
                            sheet.write(rowx, 8, (in_lot_qty != 0 and in_lot_qty * price) or '', content_float)
                            sheet.write(rowx, 9, (out_lot_qty != 0 and out_lot_qty * price) or '', content_float)
                            sheet.write(rowx, 11, first_avail_lot, content_float)
                        else:
                            sheet.write(rowx, 8, (in_qty != 0 and in_qty * price) or '', content_float)
                            sheet.write(rowx, 9, (out_qty != 0 and out_qty * price) or '', content_float)
                            sheet.write(rowx, 11, first_avail, content_float)
                        sheet.write(rowx, 10, (change != 0 and (change * first_avail)) or '', content_float)
                    else:
                        sheet.write(rowx, 7, (diff != 0 and diff) or "", content_float)
                        if seri:
                            sheet.write(rowx, 8, (in_qty != 0 and in_qty * cost) or '', content_float)
                            sheet.write(rowx, 9, (out_qty != 0 and out_qty * cost) or '', content_float)
                            sheet.write(rowx, 10, '', content_float)
                            sheet.write(rowx, 11, first_avail_lot, content_float)
                        else:
                            sheet.write(rowx, 8, (in_qty != 0 and in_qty * cost) or '', content_float)
                            sheet.write(rowx, 9, (out_qty != 0 and out_qty * cost) or '', content_float)
                            sheet.write(rowx, 10, balance or '', content_float)
                            sheet.write(rowx, 11, first_avail, content_float)
                    rowx += 1

            sheet.write(rowx, 0, '', format_group)
            sheet.write(rowx, 1, '', format_group)
            sheet.write(rowx, 2, '', format_group)
            sheet.write(rowx, 3, '', format_group)
            sheet.write(rowx, 4, '', format_group)
            sheet.write(rowx, 5, '', format_group)
            if self.report_type == 'owner':
                sheet.write(rowx, 6, _('Total'), format_group)
                if seri:
                    sheet.write(rowx, 7, in_lot_total, format_content_bold_float_color)
                    sheet.write(rowx, 8, out_lot_total, format_content_bold_float_color)
                    sheet.write(rowx, 9, first_avail_lot, format_content_bold_float_color)
                else:
                    sheet.write(rowx, 7, in_total, format_content_bold_float_color)
                    sheet.write(rowx, 8, out_total, format_content_bold_float_color)
                    sheet.write(rowx, 9, first_avail, format_content_bold_float_color)

            elif self.report_type in ("price", "cost"):
                sheet.write(rowx, 6, _('Income, Expense Total'), format_group)
                sheet.write(rowx, 7, "", format_content_bold_float_color)
                if seri:
                    sheet.write(rowx, 8, in_lot_total, format_content_bold_float_color)
                    sheet.write(rowx, 9, out_lot_total, format_content_bold_float_color)
                else:
                    sheet.write(rowx, 8, in_total, format_content_bold_float_color)
                    sheet.write(rowx, 9, out_total, format_content_bold_float_color)
                sheet.write(rowx, 10, "", format_group)
                sheet.write(rowx, 11, "", format_content_bold_float_color)
                if self.report_type == 'cost':
                    sheet.write(rowx, 7, (qty and qty) or "0.0", format_content_bold_float_color)
                    sheet.write(rowx, 10, (last_cost and first_avail and (last_cost * first_avail)) or '0.0',
                                format_content_bold_float_color)
                    sheet.write(rowx, 11, first_avail, format_content_bold_float_color)
            rowx += 1

        if self.report_type == "owner":
            sheet.write(rowx, 1, _('Check: '), format_filter)
            rowx += 3
            sheet.write(rowx, 2,
                        _('Product keeper comment: ................................................................................................'),
                        format_filter)
            sheet.write(rowx + 1, 5,
                        _('.........................................................................................................................'),
                        format_filter)
            sheet.write(rowx + 2, 2,
                        _('Conclusions and decisions on checks: ......................................................................................'),
                        format_filter)
            sheet.write(rowx + 3, 5,
                        _('.........................................................................................................................'),
                        format_filter)
            sheet.write(rowx + 4, 2,
                        _('Authorized checker: ...................................work.............................................'),
                        format_filter)
            sheet.write(rowx + 6, 2,
                        _('attended: signature: .............................................................../......................................./'),
                        format_filter)
            sheet.write(rowx + 7, 5,
                        _('signature: ........................................................................./......................................./'),
                        format_filter)
            sheet.write(rowx + 8, 2,
                        _('Product keeper: ......................................................................./......................................./'),
                        format_filter)
            sheet.write(rowx + 9, 5,
                        _('...................................................................................../......................................./'),
                        format_filter)
            sheet.write(rowx + 10, 2, _('Date: .................................'), format_filter)

        elif self.report_type in ('price', 'cost'):
            rowx += 2
            sheet.write(rowx, 2,
                        _('Accountant: ......................................................................./......................................./'),
                        format_filter)
            rowx += 2
            sheet.write(rowx, 2, _('Date: .................................'), format_filter)

        sheet.set_column(0, 0, 2)
        sheet.set_column(1, 1, 5)
        sheet.set_column(2, 4, 15)
        sheet.set_column(5, 5, 40)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 9, 8)
        sheet.set_column(10, 18, 12)

        book.close()
        report_excel_output_obj.filedata = base64.b64encode(output.getvalue())
        return report_excel_output_obj.export_report()
