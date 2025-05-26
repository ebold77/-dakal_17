# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    # name = fields.Char('Reference', default='/', copy=False)
    # sequence_id = fields.Many2one('ir.sequence', 'Statement Sequence')
    # balance_end_income = fields.Monetary('Balance Income', compute='_end_balance')
    # balance_end_outcome = fields.Monetary('Balance Outcome', compute='_end_balance')
  
    
class AccountBankStatementLine(models.Model):
    _name = "account.bank.statement.line"
    _inherit = 'account.bank.statement.line'

    bank_account_id = fields.Many2one('res.partner.bank', string='Bank')

    def print_cash_order(self):
        # Кассын баримт хэвлэх
        statement = self.browse(self.ids)
        if self.journal_id.type == 'bank':
            
            data = {
                'is_statement_line': True
            }
            print('is_statement_line====', data)
            return self.env.ref('basic_financial_documents.action_payment_assignment_line').report_action(self, data)
        else:
            print('self.amount====', self.amount)
            if self.amount > 0:
                return self.env.ref('basic_financial_documents.action_print_cash_income_order').report_action(self)
            else:
                return self.env.ref('basic_financial_documents.action_print_cash_expense_order').report_action(self)


    def onchange_partner(self, cr, uid, ids, partner_id, journal_id, context=None):
        j = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        p = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
        result = {'bank_account_id':False}
        if j and j.type == 'bank' and p and p.bank_ids:
            for bank in p.bank_ids:
                result.update({'bank_account_id':bank.id})
                return {'value':result}
        return False