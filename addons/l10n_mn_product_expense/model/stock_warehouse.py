# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockWareHouse(models.Model):
    _inherit = 'stock.warehouse'

    workflow_id = fields.Many2one('workflow.config', 'Workflow', help='Allow expense workflow by each warehouses')
    expense_account_id = fields.Many2one('account.account', string="Expense Account")
