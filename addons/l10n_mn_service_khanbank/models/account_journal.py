# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import models, fields, api
from .constants import *

class AccountJournal(models.Model):
    _inherit = "account.journal"

    bank_bic = fields.Char(related='bank_id.bic')

    def _default_outbound_payment_methods(self):
        methods = super(AccountJournal, self)._default_outbound_payment_methods()
        return methods + self.env.ref('es_bank_service_khanbank.account_payment_method_khanbank')

    @api.model
    def _enable_khanbank_on_bank_journals(self):
        """ Enables khanbank credit transfer payment method on bank journals. Called upon module installation via data file.
        """
        khanbank = self.env.ref('es_bank_service_khanbank.account_payment_method_khanbank')
        domain = ['&', ('type', '=', 'bank'), ('bank_bic', '=ilike', KHANBANK_NAME_LOWER)]
        for bank_journal in self.search(domain):
            bank_journal.write({'outbound_payment_method_ids': [(4, khanbank.id, None)]})
