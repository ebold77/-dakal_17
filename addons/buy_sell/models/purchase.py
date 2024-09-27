# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    
    purchase_type = fields.Selection([
        ('import', 'Import'),
        ('market', 'Market'),
        ('barter', 'Barter'),
        ('sale_return', 'Sale Return'),
    ], string='Purchase Type', default = 'market')