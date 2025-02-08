# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    display_name = fields.Char(compute='_compute_display_name')
    available_to_choose = fields.Boolean('Available', compute='_available')

    @api.depends('quant_ids', 'quant_ids.reserved_quantity', 'quant_ids.quantity', 'product_qty')
    def _available(self):
        for lot in self:
            if lot.product_qty <= 0:
                lot.available_to_choose = False
            elif lot.product_qty > 0:
                quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
                for q in quants:
                    if q.quantity - q.reserved_quantity > 0:
                        lot.available_to_choose = True
                    elif q.quantity - q.reserved_quantity < 0:
                        lot.available_to_choose = False

    @api.onchange('product_qty')
    def _onchange_usage(self):
        if self.product_qty > 0:
            self.available_to_choose = True
        else:
            self.available_to_choose = False

    

    @api.depends('name')  # depends on the fields that make up your name
    def _compute_display_name(self):

        for record in self:
            qty = record.product_qty
            if record.expiration_date:
                
                names = [record.name, record.expiration_date.strftime("%Y-%m-%d")]  # adjust this line based on your needs
                display_name = ' / '.join(filter(None, names))
                display_names =[display_name, str(qty)]
                record.display_name = ' | '.join(filter(None, display_names))
            else:
                # names = [record.name]  # adjust this line based on your needs
                # record.display_name = record.name
                display_names =[record.name, str(qty)]
                record.display_name = ' | '.join(filter(None, display_names))