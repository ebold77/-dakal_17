# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models, tools
from odoo.tools import pycompat, OrderedSet

from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
import re

regex_field_agg = re.compile(r'(\w+)(?::(\w+)(?:\((\w+)\))?)?')


# valid SQL aggregation functions
VALID_AGGREGATE_FUNCTIONS = {
    'array_agg', 'count', 'count_distinct',
    'bool_and', 'bool_or', 'max', 'min', 'avg', 'sum',
}
class StockReportDetail(models.Model):
    _name = "stock.report.detail"
    _rec_name = "product_id"
    _description = "Stock Report Detail"
    _auto = False
    _order = 'product_id'

    picking_id = fields.Many2one('stock.picking', 'Баримт', readonly=True)
    location_id = fields.Many2one('stock.location', 'Байрлал', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Харилцагч', readonly=True)
    date_expected = fields.Date('Огноо', readonly=True)
    date_balance = fields.Date('Эхний үлдэгдлийн огноо', readonly=True)
    product_id = fields.Many2one('product.product', 'Барааны хувилбар', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Бараа', readonly=True)
    categ_id = fields.Many2one('product.category', 'Ангилал', readonly=True,)
    account_id = fields.Many2one('account.account', 'БМ данс', readonly=True)
    uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж', readonly=True)
    description = fields.Char('Тайлбар', readonly=True)
    qty_first = fields.Float('Эхний үлдэгдэл (тоо хэмжээ)', readonly=True)
    price_unit_first = fields.Float('Эхний үлдэгдэл (нэгж өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    total_price_first = fields.Float('Эхний үлдэгдэл (нийт өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    qty_last = fields.Float('Эцсийн үлдэгдэл (тоо хэмжээ)', readonly=True)
    total_price_last = fields.Float('Эцсийн үлдэгдэл (нийт өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    qty_income = fields.Float('Орлого (тоо хэмжээ)', readonly=True)
    price_unit_income = fields.Float('Орлого (нэгж өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    total_price_income = fields.Float('Орлого (нийт өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    qty_expense = fields.Float('Зарлага (тоо хэмжээ)', readonly=True)
    price_unit_expense = fields.Float('Зарлага (нэгж өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    price_unit = fields.Float('Нэгж өртөг', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    total_price_expense = fields.Float('Зарлага (нийт өртөг)', readonly=True, groups="l10n_mn_stock_report.group_stock_see_price_unit")
    company_id = fields.Many2one('res.company', 'Компани', readonly=True, default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Бүгд'),
        ('confirmed', 'Бэлэн болохыг хүлээж байгаа'),
        ('assigned', 'Бэлэн'),
        ('done', 'Дууссан'),
    ], default='done', string='Төлөв', required=True,)
    transfer_type = fields.Selection([
        ('incoming', 'Орлого'),
        ('outgoing', 'Зарлага'),
        ('internal', 'Дотоод Хөдөлгөөн'),
    ], readonly=True, string='Шилжүүлгийн Төрөл')

    def _select(self):
        return """
            SELECT
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl.id as location_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    pt.categ_id as categ_id,
                    categ_accounts.account_id as account_id,
                    pt.uom_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    svl.unit_cost as price_unit,
                    0 as qty_first,
                    0 as price_unit_first,
                    0 as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    sml.quantity/uu.factor as qty_expense,
                    svl.unit_cost as price_unit_expense,
                    (sml.quantity/uu.factor * ABS(svl.unit_cost)) as total_price_expense,
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    wh.id as warehouse_id,
                    sml.company_id as company_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal'
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """

    def _select2(self):
        return """
            SELECT
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl2.id as location_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    pt.categ_id as categ_id,
                    categ_accounts.account_id as account_id,
                    pt.uom_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    svl.unit_cost as price_unit,
                    0 as qty_first,
                    0 as price_unit_first,
                    0 as total_price_first,
                    sml.quantity/uu.factor as qty_income,
                    svl.unit_cost as price_unit_income,
                    (sml.quantity/uu.factor * ABS(svl.unit_cost)) as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    wh2.id as warehouse_id,
                    sml.company_id as company_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal'
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """

    def _select3(self):
        return """
            SELECT
                    sml.id*-1 as id,
                    sp.partner_id as partner_id,
                    sml.location_dest_id as location_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    pt.categ_id as categ_id,
                    categ_accounts.account_id as account_id,
                    pt.uom_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    svl.unit_cost as price_unit,
                    sml.quantity/uu.factor as qty_first,
                    svl.unit_cost as price_unit_first,
                    (sml.quantity/uu.factor * ABS(svl.unit_cost)) as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    null::date as date_expected,
                    (sml.date + interval '8 hour')::date as date_balance,
                    wh.id as warehouse_id,
                    sml.company_id as company_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal'
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """

    def _select4(self):
        return """
            SELECT
                    sml.id*-33 as id,
                    sp.partner_id as partner_id,
                    sml.location_id as location_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    pt.categ_id as categ_id,
                    categ_accounts.account_id as account_id,
                    pt.uom_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    svl.unit_cost as price_unit,
                    -(sml.quantity/uu.factor) as qty_first,
                    svl.unit_cost as price_unit_first,
                    -(sml.quantity/uu.factor * ABS(svl.unit_cost)) as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    null::date as date_expected,
                    (sml.date + interval '8 hour')::date as date_balance,
                    wh.id as warehouse_id,
                    sml.company_id as company_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal'
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """

    def _select_main(self):
        return """
            SELECT
                    id,
                    partner_id,
                    location_id,
                    description,
                    state,
                    picking_id,
                    categ_id,
                    account_id,
                    uom_id,
                    product_id,
                    product_tmpl_id,
                    price_unit,
                    qty_first,
                    price_unit_first,
                    total_price_first,
                    qty_income,
                    price_unit_income,
                    total_price_income,
                    qty_expense,
                    price_unit_expense,
                    total_price_expense,
                    (qty_first+qty_income-qty_expense) as qty_last,
                    (total_price_first+total_price_income-total_price_expense) as total_price_last,
                    date_expected,
                    date_balance,
                    warehouse_id,
                    company_id,
                    transfer_type
        """

    def _from(self):
        return """
            FROM stock_move_line as sml
        """

    def _from2(self):
        return """
            FROM stock_move_line as sml
        """

    def _from3(self):
        return """
            FROM stock_move_line as sml
        """

    def _from4(self):
        return """
            FROM stock_move_line as sml
        """

    def _join(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_valuation_layer as svl on (sm.id = svl.stock_move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_warehouse as wh on (wh.lot_stock_id = sl.id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN stock_warehouse as wh2 on (wh2.lot_stock_id = sl2.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN (
                SELECT split_part(ip.res_id, ',', 2)::INTEGER as categ_id, split_part(ip.value_reference, ',', 2)::INTEGER as account_id FROM ir_property ip
                WHERE
                      ip.name = 'property_stock_valuation_account_id'
            ) AS categ_accounts
            ON categ_accounts.categ_id = pt.categ_id
        """

    def _join2(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_valuation_layer as svl on (sm.id = svl.stock_move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_warehouse as wh on (wh.lot_stock_id = sl.id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN stock_warehouse as wh2 on (wh2.lot_stock_id = sl2.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN (
                SELECT split_part(ip.res_id, ',', 2)::INTEGER as categ_id, split_part(ip.value_reference, ',', 2)::INTEGER as account_id FROM ir_property ip
                WHERE
                      ip.name = 'property_stock_valuation_account_id'
            ) AS categ_accounts
            ON categ_accounts.categ_id = pt.categ_id
        """

    def _join3(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_valuation_layer as svl on (sm.id = svl.stock_move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
            LEFT JOIN stock_warehouse as wh on (wh.lot_stock_id = sl.id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN stock_warehouse as wh2 on (wh2.lot_stock_id = sl2.id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN (
                SELECT split_part(ip.res_id, ',', 2)::INTEGER as categ_id, split_part(ip.value_reference, ',', 2)::INTEGER as account_id FROM ir_property ip
                WHERE
                      ip.name = 'property_stock_valuation_account_id'
            ) AS categ_accounts
            ON categ_accounts.categ_id = pt.categ_id
        """

    def _join4(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_valuation_layer as svl on (sm.id = svl.stock_move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_warehouse as wh on (wh.lot_stock_id = sl.id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN stock_warehouse as wh2 on (wh2.lot_stock_id = sl2.id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN (
                SELECT split_part(ip.res_id, ',', 2)::INTEGER as categ_id, split_part(ip.value_reference, ',', 2)::INTEGER as account_id FROM ir_property ip
                WHERE
                      ip.name = 'property_stock_valuation_account_id'
            ) AS categ_accounts
            ON categ_accounts.categ_id = pt.categ_id
        """

    def _where(self):
        return """"""

    def _where2(self):
        return """"""

    def _where3(self):
        return """  """

    def _where4(self):
        return """  """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
                %s
                FROM (
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                ) as temp_ariuk4
            )
        """ % (self._table, self._select_main(), self._select(), self._from(), self._join(), self._where(),
               self._select2(), self._from2(), self._join2(), self._where2(),
               self._select3(), self._from3(), self._join3(), self._where3(),
               self._select4(), self._from4(), self._join4(), self._where4())
                )
