#-*- coding: utf-8 -*-

from datetime import timedelta, datetime, date
import calendar
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.tools.misc import format_date
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.tests.common import Form


class ResCompany(models.Model):
    _inherit = "res.company"
    
    base_pricelist_id = fields.Many2one('product.pricelist', string="Default Base Pricelist")
    barter_pricelist_id = fields.Many2one('product.pricelist', string="Barter Base Pricelist")
    sale_pricelist_id = fields.Many2one('product.pricelist', string="Sale Base Pricelist")
    barter_warehouse_id = fields.Many2one('stock.warehouse', string="Default Barter Warehouse")