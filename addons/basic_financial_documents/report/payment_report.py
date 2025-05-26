# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.addons.l10n_mn_report.models.report_helper import verbose_numeric, comma_me, convert_curr
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

class PaymentReportView(models.AbstractModel):
    _name = 'report.basic_financial_documents.payment_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Кассын зарлагын баримт
        statement_line_obj = self.env['account.bank.statement.line']
        docs = statement_line_obj.browse(docids)
        report = self.env['ir.actions.report'].search([('report_name', '=', 'basic_financial_documents.print_cash_expense_order')])
        verbose_total_dict = {}
        amounts = {}
        currency = {}
        signature_lines = {}
        for doc in docs:
            word = verbose_numeric(abs(doc.amount))
            print('wwwwwwwwwwwwwwww', word)
            curr = u''
            div_curr = u''
            symbol = u''
            if doc.currency_id:
                curr = doc.statement_id.currency_id.id
                #div_curr = doc.statement_id.currency_id.divisible
                symbol = doc.currency_id.symbol
            elif doc.statement_id.currency_id:
                curr = doc.statement_id.currency_id.id
                #div_curr = doc.statement_id.currency_id.divisible
                symbol = doc.statement_id.currency_id.symbol
            verbose_total_dict[doc.id] = convert_curr(word, curr, div_curr)
            amounts[doc.id] = comma_me(abs(doc.amount))
            currency[doc.id] = {'name': curr,
                                'symbol': symbol}
            # if report:
                # Гарын үсгийн тохиргоо
                # report_lines = self.env['report.footer.config'].get_report_signature(report, doc.statement_id.company_id)
                # signature_lines[doc.id] = report_lines
        # if docs.move_id.journal_id.account_user_id:
        #     docs.user_id = docs.move_id.journal_id.account_user_id
        # if not docs.move_id.journal_id.account_user_id:
        # docs.user_id = self.env.uid
        print('verbose_total_dict', verbose_total_dict)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.bank.statement.line',
            'docs': docs,
            'verbose_amount': verbose_total_dict,
            'company_id': self.env.company,
            'amounts': amounts,
            'currency': currency,
            'user': self.env.uid,
            # 'data_report_margin_top': 20,
            # 'data_report_header_spacing': 5,
            # 'signature_lines': signature_lines,
        }
