# -*- coding: utf-8 -*-
##############################################################################

from odoo import api, fields, models
from .constants import *
import logging

_logger = logging.getLogger(__name__)

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)

    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        cur = line.order_id.pricelist_id.currency_id
        taxes = taxes.compute_all(price, cur, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)['taxes']
        val = 0.0
        for c in taxes:
            val += c.get('amount', 0.0)
        return val

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_taxes(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            line.amount_tax_vat = currency.round(self._amount_tax(line, line.order_id.fiscal_position_id, TAX_TYPE_VAT))
            line.amount_tax_city = currency.round(self._amount_tax(line, line.order_id.fiscal_position_id, TAX_TYPE_CITY))