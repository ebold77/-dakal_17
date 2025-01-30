from odoo import models

import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_dest_account(self, accounts_data):
        res = super()._get_dest_account(accounts_data)
        # get expense account
        if self.picking_id.product_expense_id:
            res = self.picking_id.product_expense_id.account_id.id
        return res
