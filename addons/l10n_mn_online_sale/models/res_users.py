#-*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.tools.misc import format_date
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.tests.common import Form


class ResUsers(models.Model):
    _inherit = "res.users"

    is_web_admin = fields.Boolean(string='Is Web Admin', default=False)