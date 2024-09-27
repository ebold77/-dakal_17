# -*- coding: utf-8 -*-

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    user_name = fields.Char('User name')
    password = fields.Char('Password')
    emd_url = fields.Char('EMD url', default = 'https://ws.emd.gov.mn/')
    user_id = fields.Many2one('res.users', 'User')
    emd_price_list_id = fields.Many2one('product.pricelist', 'EMD Price List')
    emd_partner_id = fields.Many2one('res.partner', 'EMD Partner')
    novartis_merchant_tin = fields.Char(string='Novartis Merchant Tin')