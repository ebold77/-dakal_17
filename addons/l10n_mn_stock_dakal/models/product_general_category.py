# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

class ProductGeneralCategory(models.Model):

    _name = "product.general.category"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product General Category"
    _order = 'name desc, id desc'

    name = fields.Char('Name', index=True)
    parent_id = fields.Many2one('product.general.category', 'Parent Category', index=True, ondelete='cascade')