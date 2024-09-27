# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    bs_allowed_warehouse_id = fields.Many2one('stock.warehouse', related="company_id.barter_warehouse_id", readonly=False, string='Warehouses')
    base_pricelist_id = fields.Many2one('product.pricelist', related="company_id.base_pricelist_id",  readonly=False, string='Pricelist')
    barter_pricelist_id = fields.Many2one('product.pricelist', related="company_id.barter_pricelist_id",  readonly=False, string='Barter Pricelist')
    sale_pricelist_id = fields.Many2one('product.pricelist', related="company_id.sale_pricelist_id", readonly=False, string='Sale Pricelist')
        
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        
        
        
        
        
        