# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    workflow_id = fields.Many2one('workflow.config', 'Workflow')
    type_approve_expense = fields.Selection([
        ('0', 'If the balance of the product is checked and the required quantity is not reached, it will not be approved'),
        ('1', 'Approve without checking the balance of the product')
    ], "Approve expense", default='0')