# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class SalesPerformanceReportWizard(models.TransientModel):
    _name = "sales.performance.report.wizard"
    _description = "product move detail report"

    date_start = fields.Date(required=True, string='Эхлэх огноо', default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date(required=True, string='Дуусах огноо', default=lambda *a: time.strftime('%Y-%m-%d'))
   

    def get_domain(self, domain):
        domain.append(('date_balance', '<', self.date_start))
        domain.append('&')
        domain.append(('date_expected', '<=', self.date_end))
        domain.append(('date_expected', '>=', self.date_start))
        return domain

    def open_analyze_view(self):
        domain = []
        action = self.env.ref('l10n_mn_sale_repots.action_sales_performance_report').sudo()
        vals = action.read()[0]
        vals['domain'] = self.get_domain(domain)
        return vals
