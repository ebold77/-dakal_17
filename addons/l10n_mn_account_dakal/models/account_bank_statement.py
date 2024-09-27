# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math
import base64


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"


    @api.model
    def _prepare_counterpart_move_line_vals(self, counterpart_vals, move_line=None):
        ''' Prepare values to create a new account.move.line move_line.
        By default, without specified 'counterpart_vals' or 'move_line', the counterpart line is
        created using the suspense account. Otherwise, this method is also called during the
        reconciliation to prepare the statement line's journal entry. In that case,
        'counterpart_vals' will be used to create a custom account.move.line (from the reconciliation widget)
        and 'move_line' will be used to create the counterpart of an existing account.move.line to which
        the newly created journal item will be reconciled.
        :param counterpart_vals:    A python dictionary containing:
            'balance':                  Optional amount to consider during the reconciliation. If a foreign currency is set on the
                                        counterpart line in the same foreign currency as the statement line, then this amount is
                                        considered as the amount in foreign currency. If not specified, the full balance is took.
                                        This value must be provided if move_line is not.
            'amount_residual':          The residual amount to reconcile expressed in the company's currency.
                                        /!\ This value should be equivalent to move_line.amount_residual except we want
                                        to avoid browsing the record when the only thing we need in an overview of the
                                        reconciliation, for example in the reconciliation widget.
            'amount_residual_currency': The residual amount to reconcile expressed in the foreign's currency.
                                        Using this key doesn't make sense without passing 'currency_id' in vals.
                                        /!\ This value should be equivalent to move_line.amount_residual_currency except
                                        we want to avoid browsing the record when the only thing we need in an overview
                                        of the reconciliation, for example in the reconciliation widget.
            **kwargs:                   Additional values that need to land on the account.move.line to create.
        :param move_line:           An optional account.move.line move_line representing the counterpart line to reconcile.
        :return:                    The values to create a new account.move.line move_line.
        '''
        self.ensure_one()

        statement = self.statement_id
        journal = statement.journal_id
        company_currency = journal.company_id.currency_id
        journal_currency = journal.currency_id or company_currency
        foreign_currency = self.foreign_currency_id or journal_currency or company_currency
        statement_line_rate = (self.amount_currency / self.amount) if self.amount else 0.0

        balance_to_reconcile = counterpart_vals.pop('balance', None)
        amount_residual = -counterpart_vals.pop('amount_residual', move_line.amount_residual if move_line else 0.0) \
            if balance_to_reconcile is None else balance_to_reconcile
        amount_residual_currency = -counterpart_vals.pop('amount_residual_currency', move_line.amount_residual_currency if move_line else 0.0)\
            if balance_to_reconcile is None else balance_to_reconcile

        if 'currency_id' in counterpart_vals:
            currency_id = counterpart_vals['currency_id'] or company_currency.id
        elif move_line:
            currency_id = move_line.currency_id.id or company_currency.id
        else:
            currency_id = foreign_currency.id

        if currency_id not in (foreign_currency.id, journal_currency.id):
            currency_id = company_currency.id
            amount_residual_currency = 0.0

        amounts = {
            company_currency.id: 0.0,
            journal_currency.id: 0.0,
            foreign_currency.id: 0.0,
        }

        amounts[currency_id] = amount_residual_currency
        amounts[company_currency.id] = amount_residual

        if currency_id == journal_currency.id and journal_currency != company_currency:
            if foreign_currency != company_currency:
                amounts[company_currency.id] = journal_currency._convert(amounts[currency_id], company_currency, journal.company_id, self.date)
            if statement_line_rate:
                amounts[foreign_currency.id] = amounts[currency_id] * statement_line_rate
        elif currency_id == foreign_currency.id and self.foreign_currency_id:
            if statement_line_rate:
                amounts[journal_currency.id] = amounts[foreign_currency.id] / statement_line_rate
                if foreign_currency != company_currency:
                    amounts[company_currency.id] = journal_currency._convert(amounts[journal_currency.id], company_currency, journal.company_id, self.date)
        else:
            amounts[journal_currency.id] = company_currency._convert(amounts[company_currency.id], journal_currency, journal.company_id, self.date)
            if statement_line_rate:
                amounts[foreign_currency.id] = amounts[journal_currency.id] * statement_line_rate

        if foreign_currency == company_currency and journal_currency != company_currency and self.foreign_currency_id:
            balance = amounts[foreign_currency.id]
        else:
            balance = amounts[company_currency.id]

        if foreign_currency != company_currency and self.foreign_currency_id:
            amount_currency = amounts[foreign_currency.id]
            currency_id = foreign_currency.id
        elif journal_currency != company_currency and not self.foreign_currency_id:
            amount_currency = amounts[journal_currency.id]
            currency_id = journal_currency.id
        else:
            amount_currency = amounts[company_currency.id]
            currency_id = company_currency.id
        return {
            **counterpart_vals,
            'name': counterpart_vals.get('name', move_line.name if move_line and move_line.name else '') + ' / ' + self.payment_ref,
            'move_id': self.move_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': currency_id,
            'account_id': counterpart_vals.get('account_id', move_line.account_id.id if move_line else False),
            'debit': balance if balance > 0.0 else 0.0,
            'credit': -balance if balance < 0.0 else 0.0,
            'amount_currency': amount_currency,
        }