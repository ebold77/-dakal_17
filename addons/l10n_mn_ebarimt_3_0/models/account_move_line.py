# -*- coding: utf-8 -*-

from odoo import api, fields, models
from .constants import *
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)

    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.move_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)

        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)

        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        cur = line.move_id.currency_id
        taxes = taxes.compute_all(price, cur, line.quantity, product=line.product_id, partner=line.move_id.partner_id or False)['taxes']
        val = 0.0
        for c in taxes:
            val += c.get('amount', 0.0)
        return val

    @api.depends('price_unit', 'tax_ids', 'quantity', 'discount', 'product_id')
    def _compute_taxes(self):
        for line in self:
            currency = line.move_id.currency_id
            line.amount_tax_vat = currency.round(self._amount_tax(line, line.move_id.fiscal_position_id, TAX_TYPE_VAT))
            line.amount_tax_city = currency.round(self._amount_tax(line, line.move_id.fiscal_position_id, TAX_TYPE_CITY))

    # def generate_invoice_line_json(self):
    #     data = {}
    #     data['code'] = self.product_id.code
    #     data['name'] = self.product_id.name
    #     data['measureUnit'] = self.product_id.uom_id.name
    #     data['qty'] = "%.2f" % self.quantity
    #     data['unitPrice'] = "%.2f" % self.price_unit
    #     data['totalAmount'] = "%.2f" % self.price_subtotal
    #     data['cityTax'] = "%.2f" % self.amount_tax_city
    #     data['vat'] = "%.2f" % self.amount_tax_vat
    #     data['barcode'] = self.product_id.barcode

    #     return data
