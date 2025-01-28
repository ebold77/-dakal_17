# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zero_qty_zero_cost = fields.Boolean(related='company_id.zero_qty_zero_cost', string="Show 0 when quantity is 0 on Stock Report", readonly=False)