# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.tools.translate import _
from .constants import *
import logging

_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _get_combine_statement_line_vals(self, statement, amount, payment_method):
        cashflow_id = False
        res = super(PosSession, self)._get_combine_statement_line_vals(statement, amount, payment_method)
        account = self._get_receivable_account(payment_method)
        if account.cashflow_account_ids:
            cashflow_id =  account.cashflow_account_ids[0].id
        res.update({
            'account_id': self._get_receivable_account(payment_method).id,
            'partner_id': self.user_id.partner_id.id,
            'cashflow_id': cashflow_id,
            }
            )
        return res