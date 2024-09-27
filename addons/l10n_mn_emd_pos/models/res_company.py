# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    ph_mobile = fields.Char('Mobile')