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
        if self.product_id:
            # optional_product_ids = self.order_id.get_online_product()
            # print('=========================== data ============================>>', optional_product_ids)
            qty_available = self.product_id.with_context({'warehouse': self.order_id.warehouse_id.id, 'lot_id': self.lot_id.id}).qty_available
            self.lot_available_qty = qty_available

    
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({
            'lot_id': self.lot_id.id,
        })
        return values