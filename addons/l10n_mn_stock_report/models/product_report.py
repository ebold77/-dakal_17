# -*- encoding: utf-8 -*-
##############################################################################
import calendar
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductReport(models.Model):
    _name = 'product.report'
    _inherit = ['mail.thread']
    _description = 'Product Report'

    def default_date(self):
        date = datetime.now()
        max_day_in_month = calendar.monthrange(date.year, date.month)[1]
        date = (date.replace(day=max_day_in_month) - relativedelta(months=1)).strftime('%Y-%m-%d 16:00:00')
        return date

    def get_report_view_type(self):
        report_view_type = [('qty', _('Quantity')),
                            ('qty_price', _('Quantity, Price'))]
        if self.user_has_groups('l10n_mn_stock.group_stock_view_cost'):
            report_view_type.append(('qty_cost', _('Quantity, Cost')))
            report_view_type.append(('all', _('All')))
        return report_view_type

    def _domain_warehouses(self):
         return [('id', 'in', self.env.user.allowed_warehouse_ids.ids), '|', ('company_id', '=', False),
                 ('company_id', '=', self.company_id.id or self.env.user.company_id.id)]

    def _compute_domain_location_ids(self):
        for report in self:
            location_ids = []
            if report.warehouse_ids:
                warehouses = report.warehouse_ids
            else:
                warehouses = self.env['stock.warehouse'].search([('id', 'in', report.env.user.allowed_warehouse_ids.ids), ('company_id', '=', report.company_id.id)])
            for wh in warehouses:
                loc_ids = self.env['stock.location'].search([('usage', '=', 'internal'), ('location_id', 'child_of', [wh.view_location_id.id])]).ids
                location_ids += loc_ids
            report.domain_location_ids = location_ids

    def _domain_products(self):
        prod_domain = [('type', '=', 'product')]
        if self.category_ids:
            prod_domain.append(('categ_id', 'in', self.category_ids.ids))
        if self.product_brand_ids:
            prod_domain.append(('brand_id', 'in', self.product_brand_ids.ids))
        if self.supplier_ids:
            prod_domain.append(('supplier_id', 'in', self.supplier_ids.ids))
        prod_ids = self.env['product.product'].search(prod_domain).ids
        return [('id', 'in', prod_ids)]

    name = fields.Char('Name', required=True, tracking=True, states={'approved': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Datetime('Start Date', required=True, default=default_date, tracking=True, states={'approved': [('readonly', True)]})
    date_to = fields.Datetime('End Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d 15:59:59'), tracking=True, states={'approved': [('readonly', True)]})
    group_by = fields.Selection([('no_group', 'No Group'),
                                 ('warehouse', 'Warehouse'),
                                 ('category', 'Category'),
                                 ('supplier', 'Supplier')], string='Group By', required=True, default='warehouse', tracking=True, states={'approved': [('readonly', True)]})
    group2_by = fields.Selection([('no_group', 'No Group'),
                                  ('location', 'Location'),
                                  ('category', 'Category'),
                                  ('supplier', 'Supplier'),
                                  ('brand', 'Brand')], string='Group2 By', required=True, default='category', tracking=True, states={'approved': [('readonly', True)]})
    report_view_type = fields.Selection(get_report_view_type, string='Report View Type', required=True, default='qty_price', tracking=True, states={'approved': [('readonly', True)]})
    report_filter = fields.Selection([('all', 'All'),
                               ('only_minus', 'Only Minus Residuals'),
                               ('non_zero', 'End Balance non Zero')], string='Report Filter', required=True, default='all', tracking=True, states={'approved': [('readonly', True)]})
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses', domain=_domain_warehouses)
    domain_location_ids = fields.Many2many('stock.location', compute='_compute_domain_location_ids')
    location_ids = fields.Many2many('stock.location', string='Locations', domain="[('id', 'in', domain_location_ids)]")
    category_ids = fields.Many2many('product.category', string='Categories')
    product_brand_ids = fields.Many2many('product.brand', string='Product Brands')
    product_ids = fields.Many2many('product.product', string='Products', domain=_domain_products)
    supplier_ids = fields.Many2many('res.partner', string='Supplier')
    line_ids = fields.One2many('product.report.line', 'report_id', string='Lines', readonly=True, copy=False)
    without_transit = fields.Boolean('Without Transit', default=False)
    description = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('approved', 'Approved')], string='State', default='draft', required=True, tracking=True)

    # Компани, эхлэх болон дуусах огноогоор нэр талбар бөглөгдөх
    @api.onchange('date_from', 'date_to')
    def onchange_product_report(self):
        for report in self:
            name = ''
            if report.company_id:
                name += _('%s is ') % report.company_id.name
            if report.date_from:
                name += _('[%s - ') % self.date_from
            if report.date_to:
                name += _('%s] duration Product Report') % self.date_to
            report.name = name

    @api.onchange('group_by')
    def _onchange_group_by(self):
        if self.group_by != 'warehouse':
            self.group2_by = 'no_group'

    @api.onchange('category_ids', 'product_brand_ids', 'supplier_ids')
    def _onchange_product_domain(self):
        domain = {}
        prod_domain = [('type', '=', 'product')]
        if self.category_ids and len(self.category_ids) > 0:
            prod_domain.append(('categ_id', 'in', self.category_ids.ids))
        if self.product_brand_ids and len(self.product_brand_ids) > 0:
            prod_domain.append(('brand_id', 'in', self.product_brand_ids.ids))
        if self.supplier_ids and len(self.supplier_ids) > 0:
            prod_domain.append(('supplier_id', 'in', self.supplier_ids.ids))
        domain['product_ids'] = prod_domain
        return {'domain': domain}

    def unlink(self):
        for report in self:
            if report.state != 'draft':
                raise UserError(_('Delete only draft in state'))
        return super(ProductReport, self).unlink()

    def validate(self):
        # Батлах
        self.write({'state': 'approved'})

    def action_to_draft(self):
        # Ноороглох
        self.write({'state': 'draft'})

    def _reset_dict(self):
        # Тайлангийн дэд болон нийт дүнгийн dictionary
        return {'initial_qty': 0,
                'initial_price': 0,
                'initial_cost': 0,
                'income_qty': 0,
                'income_price': 0,
                'income_cost': 0,
                'expense_qty': 0,
                'expense_price': 0,
                'expense_cost': 0,
                'end_qty': 0,
                'end_price': 0,
                'end_cost': 0,
                }

    def get_sub_line(self, sequence, group_line_id, group_line_name):
        # Тайлангийн бүлэглэлтийн мөр
        return {'sequence': sequence,
                'name': group_line_name,
                'warehouse_id': group_line_id,
                'report_id': self.id,
                'color': 'bold',
                'report_view_type': self.report_view_type
                }

    def write_sub_line(self, sub):
        # Тайлангийн бүлэглэлтийн дэд дүн
        end_qty = sub['initial_qty'] + sub['income_qty'] - sub['expense_qty']
        end_price = sub['initial_price'] + sub['income_price'] - sub['expense_price']
        end_cost = sub['initial_cost'] + sub['income_cost'] - sub['expense_cost']
        return {'initial_qty': sub['initial_qty'],
                'initial_price': sub['initial_price'],
                'initial_cost': sub['initial_cost'],
                'income_qty': sub['income_qty'],
                'income_price': sub['income_price'],
                'income_cost': sub['income_cost'],
                'expense_qty': sub['expense_qty'],
                'expense_price': sub['expense_price'],
                'expense_cost': sub['expense_cost'],
                'end_qty': end_qty,
                'end_price': end_price,
                'end_cost': end_cost
                }

    def get_group_id(self):
        # Мөрт Бүлэглэлтийн id-г
        name = ''
        if self.group_by == 'warehouse':
            name = 'warehouse_id'
        elif self.group_by == 'category':
            name = 'category_id'
        elif self.group_by == 'supplier':
            name = 'supplier_id'
        return name

    def get_group2_id(self):
        # Мөрт Бүлэглэлт 2-н id-г өгөх
        name = ''
        if self.group2_by == 'location':
            name = 'location_id'
        elif self.group2_by == 'category':
            name = 'category_id'
        elif self.group2_by == 'brand':
            name = 'product_brand_id'
        elif self.group2_by == 'supplier':
            name = 'supplier_id'
        return name

    def get_line(self, line, sequence):
        # Тайлангийн мөр
        zero = self.env.company.zero_qty_zero_cost
        end_price = end_cost = 0
        end_qty = line['initial_qty'] + line['income_qty'] - line['expense_qty']
        if self.report_view_type in ('qty_price', 'all') and not (zero and end_qty == 0):
            end_price = line['initial_price'] + line['income_price'] - line['expense_price']
        if self.report_view_type in ('qty_cost', 'all') and not (zero and end_qty == 0):
            end_cost = line['initial_cost'] + line['income_cost'] - line['expense_cost']
        vals = {'sequence': sequence,
                'initial_qty': line['initial_qty'],
                'initial_price': line['initial_price'] if self.report_view_type in ('qty_price', 'all') and not (zero and line['initial_qty'] == 0) else 0,
                'initial_cost': line['initial_cost'] if self.report_view_type in ('qty_cost', 'all') and not (zero and line['initial_qty'] == 0) else 0,
                'income_qty': line['income_qty'],
                'income_price': line['income_price'] if self.report_view_type in ('qty_price', 'all') and not (zero and line['income_qty'] == 0) else 0,
                'income_cost': line['income_cost'] if self.report_view_type in ('qty_cost', 'all') and not (zero and line['income_qty'] == 0) else 0,
                'expense_qty': line['expense_qty'],
                'expense_price': line['expense_price'] if self.report_view_type in ('qty_price', 'all') and not (zero and line['expense_qty'] == 0) else 0,
                'expense_cost': line['expense_cost'] if self.report_view_type in ('qty_cost', 'all') and not (zero and line['expense_qty'] == 0) else 0,
                'end_qty': end_qty,
                'end_price': end_price,
                'end_cost': end_cost,
                'report_id': self.id,
                'color': 'black',
                'report_view_type': self.report_view_type}
        if self.group_by != 'no_group':
            vals['name'] = line['group_name']
            id_name = self.get_group_id()
            vals[id_name] = line['group_id']
        if self.group_by == 'warehouse' and self.group2_by != 'no_group':
            vals['name'] = False
            vals['name2'] = line['group2_name']
            id2_name = self.get_group2_id()
            vals[id2_name] = line['group2_id']
        return vals

    def get_total(self, dict, line):
        # Нийт дүнгүүдийг олох
        if self.report_view_type in ('qty_price', 'all'):
            dict['initial_price'] += line['initial_price'] or 0
            dict['income_price'] += line['income_price'] or 0
            dict['expense_price'] += line['expense_price'] or 0
        if self.report_view_type in ('qty_cost', 'all'):
            dict['initial_cost'] += line['initial_cost'] or 0
            dict['income_cost'] += line['income_cost'] or 0
            dict['expense_cost'] += line['expense_cost'] or 0
        dict['initial_qty'] += line['initial_qty'] or 0
        dict['income_qty'] += line['income_qty'] or 0
        dict['expense_qty'] += line['expense_qty'] or 0

    def get_total_line(self, dict, name):
        # Тайлангийн нийт дүнгийн мөр
        end_qty = dict['initial_qty'] + dict['income_qty'] - dict['expense_qty']
        end_price = dict['initial_price'] + dict['income_price'] - dict['expense_price']
        end_cost = dict['initial_cost'] + dict['income_cost'] - dict['expense_cost']
        return {'name': name.upper(),
                'initial_qty': dict['initial_qty'],
                'initial_price': dict['initial_price'],
                'initial_cost': dict['initial_cost'],
                'income_qty': dict['income_qty'],
                'income_price': dict['income_price'],
                'income_cost': dict['income_cost'],
                'expense_qty': dict['expense_qty'],
                'expense_price': dict['expense_price'],
                'expense_cost': dict['expense_cost'],
                'end_qty': end_qty,
                'end_price': end_price,
                'end_cost': end_cost,
                'report_id': self.id,
                'color': 'blue',
                'report_view_type': self.report_view_type
                }

    def compute_line(self, line_obj, lines):
        # Тооцоолол хийн мөрүүд үүсгэх функц
        group = False
        total = self._reset_dict()
        sub = self._reset_dict()
        seq = sub_seq = 1
        for line in lines:
            # Үндсэн мөр
            sequence = _('%s') % seq
            if self.group_by == 'warehouse' and self.group2_by != 'no_group':
                group_line_id = line['group_id']        # Бүлэглэх id
                group_line_name = line['group_name']    # Бүлэглэх нэр
                if not group or group != group_line_id:
                    # Бүлэглэлт - Агуулах, Бүлэглэлт 2 - той үед Бүлэглэлт хийх
                    if group:
                        sub_val = self.write_sub_line(sub)
                        group_id.write(sub_val)
                        sub = self._reset_dict()
                        sub_seq += 1
                        seq = 1
                    sequence = _('%s') % sub_seq
                    sub_val = self.get_sub_line(sequence, group_line_id, group_line_name)
                    group_id = line_obj.create(sub_val)
                    group = line['group_id']
                # Үндсэн мөр
                sequence = _('%s.%s') % (sub_seq, seq)
            # Тайлангийн мөрийг үүсгэх
            val = self.get_line(line, sequence)
            line_obj.create(val)
            seq += 1
            # Нийт дүнг тооцоолох
            self.get_total(total, line)
            # Бүлэглэлтийн дэд дүнг тооцоолох
            self.get_total(sub, line)
        if self.group_by == 'warehouse' and self.group2_by != 'no_group':
            # Бүлэглэлт
            sub_val = self.write_sub_line(sub)
            group_id.write(sub_val)
        if self.group_by != 'no_group':
            total_val = self.get_total_line(total, _('Total'))
            line_obj.create(total_val)
        return True

    def compute(self):
        # Тайлангын утгууд олох
        self.line_ids = None
        line_obj = self.env['product.report.line']
        # Эхлэл болон тухайн хугацааны хоорондох утгыг олох
        lines = self.get_query(False)
        if lines:
            self.compute_line(line_obj, lines)
        return True

    def get_sub_where(self):
        where = ""
        if self.product_ids:
            where += ' AND pp.id in (' + ','.join(map(str, self.product_ids.ids)) + ') '
        if self.category_ids:
            category_ids = self.category_ids.ids
            where += ' AND pc.id in (' + ','.join(map(str, category_ids)) + ') '
        if self.product_brand_ids:
            where += ' AND pb.id in (' + ','.join(map(str, self.product_brand_ids.ids)) + ') '
        if self.supplier_ids:
            where += ' AND rp.id in (' + ','.join(map(str, self.supplier_ids.ids)) + ') '
        return where

    def get_where(self):
        join = ""
        where = ""
        return join, where

    def get_warehouse_join(self):
        join = "LEFT JOIN stock_location sl ON (r.lid = sl.id)"
        join += "LEFT JOIN stock_location sl1 ON (sl.location_id = sl1.id) "
        join += "LEFT JOIN stock_location sl2 ON (sl1.location_id = sl2.id) "
        join += "LEFT JOIN stock_warehouse sw ON (sw.view_location_id = sl1.id) "
        join += "LEFT JOIN stock_warehouse sw1 ON (sw1.view_location_id = sl2.id) "
        return join

    def get_query_group(self):
        # Бүлэглэлт
        join = ""
        select = ""
        sub_select = ""
        group_by = ""
        order_by = ""
        if self.group_by == 'warehouse':
            # Бүлэглэлт 1 - Агуулах
            select += "CASE WHEN sw.id IS NULL THEN  sw1.id ElSE sw.id END AS group_id, "
            select += "CASE WHEN sw.code IS NULL THEN  sw1.code ElSE sw.code END AS group_code, "
            select += "CASE WHEN sw.name IS NULL THEN  sw1.name ElSE sw.name END AS group_name, "
            join = self.get_warehouse_join()
            group_by = "GROUP BY sw.id, sw1.id, sw.code, sw1.code, sw.name, sw1.name "
            order_by = "ORDER BY sw.code, sw1.code, sw.name, sw1.name "
            if self.group2_by == 'location':
                # Бүлэглэлт 2 - Байрлал
                select += "sl.id AS group2_id, sl.name AS group2_name, "
                group_by += ", sl.id, sl.name "
                order_by += ', sl.name '
            elif self.group2_by == 'category':
                # Бүлэглэлт 2 - Ангилал
                select += " r.categ_id AS group2_id, r.categ_name AS group2_name, "
                sub_select += " pc.id AS categ_id, pc.name AS categ_name, "
                group_by += ", r.categ_id, r.categ_name "
                order_by += ", r.categ_name "
            elif self.group2_by == 'supplier':
                # Бүлэглэлт 2 - Нийлүүлэгч
                select += " r.supp_id AS group2_id, r.supp_name AS group2_name, "
                sub_select += " rp.id AS supp_id, rp.name AS supp_name, "
                group_by += ", r.supp_id, r.supp_name "
                order_by += ", r.supp_name "
            elif self.group2_by == 'brand':
                # Бүлэглэлт 2 - Барааны бренд
                select += " r.brand_id AS group2_id, r.brand_name AS group2_name, "
                sub_select += " pb.id AS brand_id, pb.name AS brand_name, "
                group_by += ", r.brand_id, r.brand_name "
                order_by += ", r.brand_name "
        elif self.group_by == 'category':
            # Бүлэглэлт 1 - Ангилал
            select += " r.categ_id AS group_id, r.categ_name AS group_name, "
            sub_select += " pc.id AS categ_id, pc.name AS categ_name, "
            group_by += "GROUP BY r.categ_id, r.categ_name "
            order_by += "ORDER BY r.categ_name "
        elif self.group_by == 'supplier':
            # Бүлэглэлт 1 - Нийлүүлэгч
            select += " r.supp_id AS group_id, r.supp_name AS group_name, "
            sub_select += " rp.id AS supp_id, rp.name AS supp_name, "
            group_by += "GROUP BY r.supp_id, r.supp_name "
            order_by += "ORDER BY r.supp_name "
        return select, sub_select, join, group_by, order_by

    def get_current_cost(self):
        # Одоогийн өртөг харуулах
        join = "LEFT JOIN (SELECT split_part(res_id, ',', 2)::int AS prod_id, value_float AS current_cost FROM ir_property " \
               "WHERE name='standard_price' AND company_id = " + str(self.company_id.id) + ") AS ip ON (r.prod_id = ip.prod_id) "
        select = "ip.current_cost AS current_cost , "
        group_by = ", ip.current_cost "
        return join, select, group_by

    def get_query(self, is_product):
        # Бараа материалын товчоо тайлангийн эхний үлдэгдэл болон тайлант хугацааны хоорондох дүнг олно.
        sub_where = self.get_sub_where()
        where_join, where = self.get_where()
        location_obj = self.env['stock.location']
        locations = []
        date_from = datetime.strftime(self.date_from, '%Y-%m-%d %H:%M:%S')
        date_to = datetime.strftime(self.date_to, '%Y-%m-%d %H:%M:%S')
        if self.env.context.get('date_field', False):
            date_field = self.env.context.get('date_field')
            date_from = datetime.strftime(date_field['date_from'], '%Y-%m-%d %H:%M:%S')
            date_to = datetime.strftime(date_field['date_to'], '%Y-%m-%d %H:%M:%S')
        if self.warehouse_ids:
            warehouses = self.warehouse_ids
        else:
            warehouses = self.env.user.allowed_warehouse_ids
        for wh in warehouses:
            # Байрлалуудыг олох
            if self.location_ids:
                locations = self.location_ids.ids
            else:
                loc_id = location_obj.search([('usage', '=', 'internal'), ('location_id', 'child_of', [wh.view_location_id.id]), '|', ('active', '=', True), ('active', '=', False)]).ids
                if loc_id:
                    locations += loc_id
        if not len(locations) > 0:
            raise UserError(_('Stock Location not found!'))
        locations = '(' + ', '.join(map(str, locations)) + ')'
        select, sub_select, join, group_by, order_by = self.get_query_group()
        if is_product:
            # Экселээр тайланг гаргах
            sort = self.env.context.get('sort', False)
            sort_order = 'r.name, r.code, '
            if sort == 'code':
                sort_order = 'r.code, r.name, '
            select += " r.prod_id AS prod_id, r.name AS name, r.code AS code, r.uom_name AS uom_name, "
            if self.group_by == 'no_group':
                group_by = "GROUP BY r.name, r.code, r.prod_id, r.uom_name "
                order_by = "ORDER BY " + sort_order + " r.prod_id, r.uom_name "
            else:
                group_by += ", r.name, r.code, r.prod_id, r.uom_name "
                order_by += ", " + sort_order + " r.prod_id, r.uom_name "
        # Эксел тайлангийн нэмэлт талбарууд
        show_field = self.env.context.get('show_field', False)
        if show_field:
            if show_field['show_barcode']:
                # Барааны зураасан код харуулах
                select += " r.barcode AS barcode, "
                sub_select += " COALESCE(pp.barcode, '') AS barcode, "
                group_by += ", r.barcode "
            if show_field['show_worthy_balance']:
                # Барааны зохистой нөөц харуулах
                select += " r.worthy_balance AS worthy_balance, "
                sub_select += " COALESCE(pt.worthy_balance, 0) AS worthy_balance, "
                group_by += ", r.worthy_balance "
            if show_field['show_qty_on_reserved']:
                # Нөөцөлсөн тоо хэмжээг харуулах
                select += "SUM(r.qty_on_reserved) AS qty_on_reserved, "
                sub_select += "CASE WHEN m.date <= '" + date_to + "' AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'assigned' "
                sub_select += "THEN COALESCE(m.product_uom_qty / u.factor * u2.factor, 0) "
                sub_select += "WHEN m.date <= '" + date_to + "' AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'assigned' "
                sub_select += "THEN -COALESCE(m.product_uom_qty / u.factor * u2.factor, 0) ELSE 0 END AS qty_on_reserved, "
            if show_field['show_qty_on_hand']:
                # Гарт байгаа тоо хэмжээг харуулах
                hand_select = hand_join = hand_group_by = hand_on = ""
                if self.group_by == 'warehouse':
                    hand_select = "CASE WHEN sw.id IS NULL THEN  sw1.id ElSE sw.id END AS wid, "
                    hand_join = "LEFT JOIN stock_location sl ON (q.location_id = sl.id)"
                    hand_join += "LEFT JOIN stock_location sl1 ON (sl.location_id = sl1.id) "
                    hand_join += "LEFT JOIN stock_location sl2 ON (sl1.location_id = sl2.id) "
                    hand_join += "LEFT JOIN stock_warehouse sw ON (sw.view_location_id = sl1.id) "
                    hand_join += "LEFT JOIN stock_warehouse sw1 ON (sw1.view_location_id = sl2.id) "
                    hand_group_by = ", sw.id, sw1.id "
                    hand_on = "  AND (sw.id = sq.wid OR sw1.id = sq.wid) "
                    if self.group2_by == 'location':
                        hand_select += "q.location_id AS lid, "
                        hand_group_by += ", q.location_id "
                        hand_on += "  AND r.lid = sq.lid"
                join += "JOIN (SELECT q.product_id AS prod_id, " + hand_select + " SUM(COALESCE(q.quantity, 0)) AS qty_on_hand FROM stock_quant q " + hand_join + " "
                join += "WHERE q.location_id IN " + locations + "GROUP BY q.product_id " + hand_group_by + ") AS sq ON (r.prod_id = sq.prod_id" + hand_on + " ) "
                select += "sq.qty_on_hand AS qty_on_hand, "
                group_by += ", sq.qty_on_hand "
            if show_field['show_current_cost'] and self.report_view_type in ('qty_cost', 'all'):
                # Одоогийн өртөг харуулах
                show_join, show_select, show_group_by = self.get_current_cost()
                join += show_join
                select += show_select
                group_by += show_group_by
        sub_join = ""
        if self.without_transit:
            # Нөхөн дүүргэлт тооцохгүй
            sub_join += "LEFT JOIN stock_location sl1 ON (m.location_id = sl1.id) "
            sub_join += "LEFT JOIN stock_location sl2 ON (m.location_dest_id = sl2.id) "
            sub_where += "AND sl1.usage != 'transit' AND sl2.usage != 'transit' AND m.location_id != m.location_dest_id "

        having = " HAVING ROUND(SUM(r.initial_qty)::decimal,4) <> 0 OR ROUND(SUM(r.income_qty)::decimal,4) <> 0 OR ROUND(SUM(r.expense_qty)::decimal,4) <> 0 "
        if self.report_view_type in ('qty_cost', 'all'):
            # Тайлан харах төрөл: Тоо ширхэг - Өртөг, Бүгд
            select += "SUM(r.initial_cost) AS initial_cost, SUM(r.income_cost) AS income_cost, SUM(r.expense_cost) AS expense_cost, "
            # с1 өртөг
            sub_select += "CASE WHEN m.date < '" + date_from + "' AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN COALESCE(m.price_unit * m.product_uom_qty, 0) "
            sub_select += "WHEN m.date < '" + date_from + "' AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN -COALESCE(m.price_unit * m.product_uom_qty, 0) ELSE 0 END AS initial_cost, "
            # Орлогын өртөг
            sub_select += "CASE WHEN m.date BETWEEN '" + date_from + "' AND '" + date_to + "' "
            sub_select += "AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN COALESCE(m.price_unit * m.product_uom_qty, 0) ELSE 0 END AS income_cost, "
            # Зарлагын өртөг
            sub_select += "CASE WHEN m.date BETWEEN '" + date_from + "' AND '" + date_to + "' "
            sub_select += "AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN COALESCE(m.price_unit * m.product_uom_qty, 0) ELSE 0 END AS expense_cost, "
            having += " OR ROUND(SUM(r.initial_cost)::decimal,4) <> 0 OR ROUND(SUM(r.income_cost)::decimal,4) <> 0 OR ROUND(SUM(r.expense_cost)::decimal,4) <> 0 "

        if self.report_view_type in ('qty_price', 'all'):
            # Тайлан харах төрөл: Тоо ширхэг - Зарах үнэ, Бүгд
            select += "SUM(r.initial_price) AS initial_price, SUM(r.income_price) AS income_price, SUM(r.expense_price) AS expense_price, "
            # с1 үнэ
            sub_select += "CASE WHEN m.date < '" + date_from + "' AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN COALESCE(pt.list_price * m.product_uom_qty, 0) "
            sub_select += "WHEN m.date < '" + date_from + "' AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN -COALESCE(pt.list_price * m.product_uom_qty, 0) ELSE 0 END AS initial_price, "
            # Орлогын үнэ
            sub_select += "CASE WHEN m.date BETWEEN '" + date_from + "' AND '" + date_to + "' "
            sub_select += "AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN COALESCE(pt.list_price * m.product_uom_qty, 0) ELSE 0 END AS income_price, "
            # Зарлагын үнэ
            sub_select += "CASE WHEN m.date BETWEEN '" + date_from + "' AND '" + date_to + "' "
            sub_select += "AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' "
            sub_select += "THEN COALESCE(pt.list_price * m.product_uom_qty, 0) ELSE 0 END AS expense_price, "

        if self.report_filter == 'only_minus':
            # Зөвхөн хасах үлдэгдэлтэйг харах
            having = " HAVING ROUND(SUM(r.initial_qty + r.income_qty - r.expense_qty)::decimal,4) < 0"
        elif self.report_filter == 'non_zero':
            # 0 үлдэгдэлтэй барааг харуулахгүй
            having = " HAVING ROUND(SUM(r.initial_qty + r.income_qty - r.expense_qty)::decimal,4) <> 0"
        # Тайлангийн үндсэн query
        self._cr.execute("SELECT " + select + " SUM(r.initial_qty) AS initial_qty, SUM(r.income_qty) AS income_qty, SUM(r.expense_qty) AS expense_qty "
                         "FROM (SELECT m.product_id AS prod_id, pp.default_code AS code, pt.name AS name, u2.name AS uom_name, " + sub_select + " "
                                    "CASE WHEN m.date < %s AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "
                                               "THEN COALESCE(m.product_uom_qty / u.factor * u2.factor, 0) "
                                         "WHEN m.date < %s AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' "  
                                               "THEN -COALESCE(m.product_uom_qty / u.factor * u2.factor, 0) ELSE 0 END AS initial_qty, "
                                    "CASE WHEN m.date BETWEEN %s AND %s AND m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "
                                               "THEN COALESCE(m.product_uom_qty / u.factor * u2.factor, 0) ELSE 0 END AS income_qty, "
                                    "CASE WHEN m.date BETWEEN %s AND %s AND m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' "
                                           "THEN COALESCE(m.product_uom_qty / u.factor * u2.factor, 0) ELSE 0 END AS expense_qty, "
                                    "CASE WHEN m.location_id NOT IN " + locations + " AND m.location_dest_id IN " + locations + " AND m.state = 'done' "  
                                               "THEN m.location_dest_id "
                                         "WHEN m.location_id IN " + locations + " AND m.location_dest_id NOT IN " + locations + " AND m.state = 'done' " 
                                               "THEN m.location_id ELSE 0 END AS lid "                                                                                      
                                "FROM stock_move m "
                                "LEFT JOIN product_product pp ON (pp.id = m.product_id) "
                                "LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id) "
                                "LEFT JOIN uom_uom u ON (u.id = m.product_uom) "
                                "LEFT JOIN uom_uom u2 ON (u2.id = pt.uom_id) "
                                "LEFT JOIN product_category pc ON (pt.categ_id = pc.id) "  
                                "LEFT JOIN product_brand pb ON (pb.id = pt.brand_id) "    
                                "LEFT JOIN res_partner rp ON (pt.supplier_id = rp.id) " + sub_join + " "                                           
                                "WHERE m.company_id = %s" + sub_where + ") AS r " + join + where_join + where + group_by + having + order_by,
                         (date_from, date_from, date_from, date_to, date_from, date_to, self.company_id.id))
        return self._cr.dictfetchall()


class ProductReportLine(models.Model):
    _name = 'product.report.line'
    _description = 'Product Report Line'

    sequence = fields.Char('Sequence')
    name = fields.Char('Group')
    name2 = fields.Char('Group2')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_id = fields.Many2one('stock.location', string='Location')
    category_id = fields.Many2one('product.category', string='Category')
    product_brand_id = fields.Many2one('product.brand', string='Product Brand')
    product_id = fields.Many2one('product.product', string='Product')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    report_id = fields.Many2one('product.report', string='Product Report', ondelete='cAScade')
    initial_qty = fields.Float(string='Initial Quantity', digits=(16, 2), default=0)
    initial_price = fields.Float(string='Initial Price', digits=(16, 2), default=0)
    initial_cost = fields.Float(string='Initial Cost', digits=(16, 2), default=0)
    income_qty = fields.Float(string='Income Quantity', digits=(16, 2), default=0)
    income_price = fields.Float(string='Income Price', digits=(16, 2), default=0)
    income_cost = fields.Float(string='Income Cost', digits=(16, 2), default=0)
    expense_qty = fields.Float(string='Expense Quantity', digits=(16, 2), default=0)
    expense_price = fields.Float(string='Expense Price', digits=(16, 2), default=0)
    expense_cost = fields.Float(string='Expense Cost', digits=(16, 2), default=0)
    end_qty = fields.Float(string='End Quantity', digits=(16, 2), default=0)
    end_price = fields.Float(string='End Price', digits=(16, 2), default=0)
    end_cost = fields.Float(string='End Cost', digits=(16, 2), default=0)
    report_view_type = fields.Selection(related='report_id.report_view_type', string='Report View Type')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    color = fields.Selection([('black', 'Black'),
                              ('bold', 'Bold'),
                              ('blue', 'Blue')], string='Color', default='black')