from odoo import models, fields, api, _
from .constants import *


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    # income = fields.Monetary(digits=0, currency_field='journal_currency_id', compute='_compute_bank_statement_value')
    # withdraw = fields.Monetary(digits=0, currency_field='journal_currency_id', compute='_compute_bank_statement_value')
    # balance = fields.Monetary(digits=0, currency_field='journal_currency_id', compute='_compute_bank_statement_value')
    #
    # @api.depends('amount')
    # def _compute_bank_statement_value(self):
    #     self.income = self.amount if self.amount >= 0 else False
    #     self.withdraw = self.amount if self.amount < 0 else False
    #     self.env.cr.execute("""
    #                 SELECT COALESCE(SUM(amount), 0) as sum
    #                 FROM account_bank_statement_line
    #                 WHERE statement_id = %s AND id <= %s""",
    #                         (self.statement_id.id, self.id))
    #     self.balance = self.env.cr.fetchone()[0]
    #     self.balance += self.statement_id.balance_start
