# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"
 
    ebarimt_service_host = fields.Char(string="Service Host", required=True, default='localhost')
    ebarimt_service_port = fields.Char(string="Service Port", required=True, default=7080)
    aimag_district_id = fields.Many2one('ebarimt.aimag.district', string="Aimag/District", help="This Aimag/District will be assigned by default on new EBarimt put operation.")
    merchant_tin = fields.Char(string='Merchant Tin')