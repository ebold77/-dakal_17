#-*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.tools.misc import format_date
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.tests.common import Form


class ResCompany(models.Model):
    _inherit = "res.company"
    
    online_warehouse_id = fields.Many2one('stock.warehouse', string="Online Warehouse")
    online_sale_pricelist_id = fields.Many2one('product.pricelist', string="Online Sale Pricelist")