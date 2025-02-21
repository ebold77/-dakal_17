#-*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.tools.misc import format_date
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.tests.common import Form


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_brand_parent = fields.Boolean(string='Is Brand Parent', default=False)