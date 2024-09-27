# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class es_report_account_payment(models.AbstractModel):
    _name = 'report.l10n_mn_ebarimt_3_0.report_payment_receipt'
    _description = 'Report Payment'

    @api.model
    def _get_report_values(self, docids, data=None):
        active_ids = self.env.context.get('active_ids', [])
        docs = self.env[data['model']].browse(active_ids)
        return {'doc_ids': active_ids,
                'doc_model': data['model'],
                'data': data,
                'docs': docs
                }
