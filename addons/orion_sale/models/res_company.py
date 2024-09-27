#-*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.tools.misc import format_date
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.tests.common import Form


class ResCompany(models.Model):
    _inherit = "res.company"
    
    orion_warehouse_id = fields.Many2one('stock.warehouse', string="OrionWarehouse")
    orion_base_pricelist_id = fields.Many2one('product.pricelist', string="Orion Base Pricelist")
    orion_sale_pricelist_id = fields.Many2one('product.pricelist', string="Orion Base Pricelist")