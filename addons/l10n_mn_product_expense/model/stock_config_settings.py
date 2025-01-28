# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    workflow_id = fields.Many2one('workflow.config', related='company_id.workflow_id', readonly=False, string="Workflow")
    type_approve_expense = fields.Selection(related="company_id.type_approve_expense", string="Approve expense", readonly=False)

    @api.model
    def get_default_wk(self, fields):
        return {'workflow_id': self.env.company.workflow_id.id}