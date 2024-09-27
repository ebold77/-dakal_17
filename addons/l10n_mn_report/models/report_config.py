# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReportFooterConfig(models.Model):
    _name = 'report.footer.config'
    _description = "All Report Footer Configure"

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name', size=128)
    report_id = fields.Many2one('ir.actions.report', string='Report')
    company_id = fields.Many2one('res.company', string='Company')

    @api.onchange('report_id')
    def onchange_type(self):
        if self.report_id:
            self.update({'name': _('%s report footer configure.') % (self.report_id.name)})

    def get_report_signature(self, report, company):
        report_lines = []
        report_conf = self.env['report.footer.config'].search(['|',('company_id', '=', False),('company_id', 'in', company.ids),('report_id', '=', report.id)], limit=1)
        for line in report_conf.line_ids:
            partner_name = ""
            if line.partner_id and line.partner_id.name:
                partner_name = line.partner_id.name
            if line.job_title:
                partner_name = partner_name + ', ' + line.job_title
            report_line = {
                'name': line.name,
                'partner': partner_name,
                'signature': line.signature,
            }
            report_lines.append(report_line)
        return report_lines

class ReportFooterConfigLine(models.Model):
    _name = 'report.footer.config.line'
    _description = 'All Report Footer Configure Line'

    name = fields.Char(string='Name', size=128)
    job_title = fields.Char(string='Job Title')
    config_id = fields.Many2one('report.footer.config', string='Report Footer Config', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=1)
    partner_id = fields.Many2one('res.partner', string='Partner')
    signature = fields.Binary('Signature')
    company_id = fields.Many2one('res.company',related='config_id.company_id', string='Company', store=True)

    _sql_constraints = [
        ('sequence_nonzero', 'check(sequence > 0)',
         'Sequence must be greater than zero!')
    ]

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.job_title = self.partner_id.function

class ReportFooterConfig(models.Model):
    _inherit = 'report.footer.config'

    line_ids = fields.One2many('report.footer.config.line', 'config_id', 'Config Line')