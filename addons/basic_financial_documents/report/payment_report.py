# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.addons.l10n_mn_report.models.report_helper import verbose_numeric, comma_me, convert_curr
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

class PaymentReportView(models.AbstractModel):
    _name = 'report.basic_financial_documents.payment_report_view'

    @api.model
    def _get_report_values(self, docids, data=None):
        if 'is_statement_line' in data:
            report = self.env['ir.actions.report'].search([('report_name', '=', 'basic_financial_documents.payment_report_view_from_statement')])
            statement_line_obj = self.env['account.bank.statement.line']
            lines = statement_line_obj.browse(self.env.context['active_ids'])
            lines = lines.filtered(lambda line: line.statement_id.journal_id.type == 'bank' and line.amount < 0)
            if not lines:
                raise UserError(_(
                    'There is nothing to print.\nCheck Journal type (Journal type should only be bank) or amount should only be outcome'))
        else:
            report = self.env['ir.actions.report'].search([('report_name', '=', 'basic_financial_documents.payment_report_view')])
            statement_line_obj = self.env['account.payment']
            lines = statement_line_obj.browse(docids)
            lines = lines.filtered(lambda line : line.payment_type == 'outbound')
            if not lines:
                raise UserError(_('There is nothing to print.\nCheck Payment type (Payment type should only be outbound)'))
        verbose_total_dict = {}
        amounts = {}
        company_data = {}
        currency = {}
        signature_lines = {}
        if not lines[0].partner_id:
            lines[0].partner_id = lines[0].company_id.partner_id.id
        for line in lines:
            word = verbose_numeric(abs(line.amount))
            curr = u''
            div_curr = u''
            symbol = False
            if line.currency_id:
                curr = line.currency_id.id
                # div_curr = line.currency_id.divisible
                symbol = line.currency_id.symbol
            elif line.account_id and line.account_id.currency_id:
                curr = line.account_id.currency_id.id
                # div_curr = line.account_id.currency_id.divisible
                symbol = line.account_id.currency_id.symbol
            elif line.statement_id and line.statement_id.journal_id and line.statement_id.journal_id.currency_id:
                curr = line.statement_id.journal_id.currency_id.id
                # div_curr = line.statement_id.journal_id.currency_id.divisible
                symbol = line.statement_id.journal_id.currency_id.symbol
            elif line.statement_id and line.statement_id.company_id and line.statement_id.company_id.currency_id:
                curr = line.statement_id.company_id.currency_id.id
                # div_curr = line.statement_id.company_id.currency_id.divisible
                symbol = line.statement_id.company_id.currency_id.symbol
            verbose_total_dict[line.id] = convert_curr(word, curr, div_curr)
            amounts[line.id] = comma_me(abs(line.amount))
            currency[line.id] = {'name': curr,
                                 'symbol': symbol}
            # if report:
                # Гарын үсгийн тохиргоо
                # report_lines = self.env['report.footer.config'].get_report_signature(report, line.company_id)
                # signature_lines[line.id] = report_lines
        return {
            'doc_ids': self.env.context['active_ids'] if 'active_ids' in self.env.context else docids,
            'doc_model': report.model,
            'docs': lines,
            'amounts': amounts,
            'partners': company_data,
            'currency': currency,
            # 'signature_lines': report_lines,
            'verbose_amount': verbose_total_dict,
            # 'data_report_margin_top': 30,
            # 'data_report_header_spacing': 5
        }
