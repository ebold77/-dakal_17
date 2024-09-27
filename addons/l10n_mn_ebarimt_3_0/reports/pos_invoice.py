# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class PosInvoiceReport(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super(PosInvoiceReport, self)._get_report_values(docids, data)
        res['docs'].ensure_one()
        ebarimt = res['docs'][0].send_ebarimt()
        res['data'] = {'lottery_no': ebarimt['lottery'],
                       'qr_data': ebarimt['qrData'],
                       }
        return res
