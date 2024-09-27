# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ebarimt_tax_type(models.Model):
    _name = 'ebarimt.tax.type'
    _description = 'EBarimt tax type'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)