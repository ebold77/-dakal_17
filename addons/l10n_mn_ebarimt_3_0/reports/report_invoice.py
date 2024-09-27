# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class es_report_account_invoice(models.AbstractModel):
    _name = 'report.l10n_mn_ebarimt_3_0.report_invoice_receipt'
    _description = 'Report Invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        active_ids = self.env.context.get('active_ids', [])
        docs = self.env[data['model']].browse(active_ids)
        qr_code_urls = {}
        for invoice in docs:
            if invoice.display_qr_code:
                new_code_url = invoice.generate_qr_code()
                if new_code_url:
                    qr_code_urls[invoice.id] = new_code_url
        print('print data', data)
        return {'doc_ids': active_ids,
                'doc_model': data['model'],
                'data': data,
                'docs': docs,
                'qr_code_urls': qr_code_urls,
                }
