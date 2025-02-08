# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, models, _
from .constants import *

class AccountJournalDashboard(models.Model):
    _inherit = "account.journal"

    def get_journal_dashboard_datas(self):
        domain_khanbank_to_send = [
            ('journal_id', '=', self.id),
            ('payment_method_id.code', '=', KHANBANK_NAME_LOWER),
            ('state', '=', 'posted')
        ]
        return dict(
            super(AccountJournalDashboard, self).get_journal_dashboard_datas(),
            num_khanbank_to_send=self.env['account.payment'].search_count(domain_khanbank_to_send)
        )

    def action_khanbank_to_send(self):
        return {
            'name': _('Khanbank Credit Transfers to Send'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form,graph',
            'res_model': 'account.payment',
            'context': dict(
                self.env.context,
                search_default_aba_to_send=1,
                journal_id=self.id,
                default_journal_id=self.id,
                default_payment_type='outbound',
                default_payment_method_id=self.env.ref('es_bank_service_khanbank.account_payment_method_khanbank').id,
            ),
        }
