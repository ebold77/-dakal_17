# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_account_bank_service_khanbank = fields.Boolean('Khanbank Corporate Gateway Service', readonly=False,
                                                          related='company_id.module_account_bank_service_khanbank')
    khanbank_base_url = fields.Char('Base URL', readonly=False, related='company_id.khanbank_base_url',
                                    help="Base URL given from Khanbank.")
    khanbank_username = fields.Char('Username', readonly=False, related='company_id.khanbank_username',
                                    help='Username given from Khanbank')
    khanbank_password = fields.Char('Password', readonly=False, related='company_id.khanbank_password',
                                    help='Password given from Khanbank')