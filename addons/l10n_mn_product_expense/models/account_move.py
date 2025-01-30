from odoo import api, models

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # @api.depends('product_id', 'account_id', 'partner_id', 'date')
    # def _compute_analytic_account_id(self):
    #     res = super()._compute_analytic_account_id()
    #     # set analytic account
    #     for aml in self:
    #         if aml.move_id.stock_move_id and aml.move_id.stock_move_id.picking_id and aml.move_id.stock_move_id.picking_id.product_expense_id:  # Шаардахаас үүссэн
    #             if aml.move_id.stock_move_id.picking_id.product_expense_id.account_id == aml.account_id:  # Зардлын данс бол
    #                 aml.analytic_account_id = aml.move_id.stock_move_id.picking_id.product_expense_id.account_analytic_id
    #     return res

    # @api.depends('product_id', 'account_id', 'partner_id', 'date')
    # def _compute_analytic_tag_ids(self):
    #     res = super()._compute_analytic_tag_ids()
    #     # set analytic tag
    #     for aml in self:
    #         if aml.move_id.stock_move_id and aml.move_id.stock_move_id.picking_id and aml.move_id.stock_move_id.picking_id.product_expense_id:  # Шаардахаас үүссэн
    #             if aml.move_id.stock_move_id.picking_id.product_expense_id.account_id == aml.account_id:  # Зардлын данс бол
    #                 aml.analytic_tag_ids = aml.move_id.stock_move_id.picking_id.product_expense_id.analytic_tag_ids
    #     return res
