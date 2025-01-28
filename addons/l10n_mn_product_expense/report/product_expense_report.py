# -*- coding: utf-8 -*-
from odoo import api, models


class ProductExpenseReport(models.AbstractModel):
    _name = 'report.l10n_mn_product_expense.report_product_expense'
    _description = 'Report Product Expense'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_lines = []
        signature_lines = {}
        docs = self.env['product.expense'].browse(docids)
        report = self.env['ir.actions.report'].search([('report_name','=','l10n_mn_product_expense.report_product_expense')])
        if report:
            for doc in docs:
                report_lines = self.env['report.footer.config'].get_report_signature(report, doc.company_id)
                signature_lines[doc.id] = report_lines
        return {
            'doc_ids': docs.ids,
            'doc_model': 'product.expense',
            'signature_lines' : signature_lines,
            'docs': docs
        }