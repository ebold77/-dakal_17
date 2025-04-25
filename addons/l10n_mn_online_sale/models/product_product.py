#-*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.tools.misc import format_date
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.tests.common import Form


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_online = fields.Boolean(string='Is Online Product', related='product_tmpl_id.is_online',)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_online = fields.Boolean(string='Is Online Product', default=False)