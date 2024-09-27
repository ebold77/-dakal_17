from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_rewards = fields.Boolean(string='is Rewards')