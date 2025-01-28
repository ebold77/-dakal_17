# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    zero_qty_zero_cost = fields.Boolean('Show 0 when quantity is 0 on Stock Report', default=False)