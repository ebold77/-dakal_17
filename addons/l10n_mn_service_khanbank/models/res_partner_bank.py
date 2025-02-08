# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import models, fields
from lxml import etree
from .constants import *

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def getBankBalance(self):
        resp_json = self.env['account.online.provider']._khanbank_fetch('GET',
                                                                        'accounts/{}/balance'.format(self.acc_number))
        account = resp_json.get('account')
        lang = self.env['res.lang']._lang_get(self.env.user.lang)
        value = str(account.get('avalaibleBalance'))
        return float(value.replace(lang.thousands_sep, '')
                     .replace(lang.decimal_point, '.'))