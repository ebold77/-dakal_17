# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from cryptography.fernet import Fernet
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .constants import *


class ResCompany(models.Model):
    _inherit = "res.company"

    module_account_bank_service_khanbank = fields.Boolean('Khanbank Corporate Gateway Service', default=False)
    khanbank_base_url = fields.Char('Base URL', size=50,
                                    help="Base URL given from Khanbank.")
    khanbank_username = fields.Char('Username', help='Username given from Khanbank', inverse='_set_khanbank_username')
    khanbank_password = fields.Char('Password', help='Password given from Khanbank', inverse='_set_khanbank_password')

    def encrypt(self, secretData):
        if not ENCTYPTION_KEY:
            raise ValidationError(_(
                "No '%s' entry found in models/constants file. "
                "Use a key similar to: %s") % ('ENCTYPTION_KEY', Fernet.generate_key())
                                  )
        key = ENCTYPTION_KEY.encode()
        f = Fernet(key)
        return f.encrypt(bytes(secretData, 'utf-8') or '').decode()

    def _set_khanbank_username(self):
        for rec in self:
            if rec.khanbank_username and len(rec.khanbank_username) < 100:
                rec.khanbank_username = rec.encrypt(rec.khanbank_username)

    def _set_khanbank_password(self):
        for rec in self:
            if rec.khanbank_password and len(rec.khanbank_password) < 100:
                rec.khanbank_password = rec.encrypt(rec.khanbank_password)
