# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    online_warehouse_id = fields.Many2one('stock.warehouse', related="company_id.online_warehouse_id", readonly=False, string='Online Warehouse')
    online_sale_pricelist_id = fields.Many2one('product.pricelist', related="company_id.online_sale_pricelist_id",  readonly=False, string='Sale Pricelist')
        
    def set_values(self):
        super(ResConfigSettings, self).set_values()