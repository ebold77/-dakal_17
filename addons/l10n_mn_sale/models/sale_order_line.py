# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_domain = [
            ('product_id', '=', 'product_id'),
            ('product_qty', '>', 0),
        ]

    lot_id = fields.Many2one(comodel_name='stock.lot', string='Seial', 
         check_company=True)
    lot_available_qty = fields.Float(string="Available QTY")

    @api.onchange('lot_id')
    def _onchange_serial_number(self):
        print('asdasdsa', self.lot_id.product_expiry_alert)
        if self.product_id:
        
            qty_available = self.product_id.with_context({'warehouse': self.order_id.warehouse_id.id, 'lot_id': self.lot_id.id}).qty_available
            self.lot_available_qty = qty_available