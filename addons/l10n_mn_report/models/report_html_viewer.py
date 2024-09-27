# -*- coding: utf-8 -*-
from odoo import models, fields


class ReportExcelHtml(models.AbstractModel):
    _name = 'oderp.report.html.output'
    _description = "Excel Report html"

    report_id = fields.Many2one('oderp.report.excel.output')

    def see_report(self):
        return {
            'type': 'ir.actions.do_nothing',
        }

    def set_report_id(self):
        self.report_id = self.with_context({'oderp_report_html': True}).export_report()

    def get_report_data(self):
        file_data = self.report_id.get_excel_file_value()
        return file_data

    def get_report_merge(self):
        file_merge = self.report_id.get_excel_file_merge()
        return file_merge

    def export_report(self):
        return True
