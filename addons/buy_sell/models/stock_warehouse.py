# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    can_barter = fields.Boolean("Can Do Barter")