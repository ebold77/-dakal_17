# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleContract(models.Model):
    _name = 'sale.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Sale\'s Contract"
    _order = 'start_date desc, id desc'

    @api.depends('totalAmt', 'order_ids.amount_total', 'invoice_ids.amount_total')
    def _amount_all(self):
        for contract in self:
            invoice_total = payment_total = 0
            sale_total = percentage = 0
    
            for order in contract.order_ids:
                sale_total += order.amount_total
            #     sales_amount += line.list_price_total
            for invoice in contract.invoice_ids:
                invoice_total += invoice.amount_total
                if invoice.amount_residual != invoice.amount_total:
                    payment_total+= invoice.amount_total - invoice.amount_residual
            totalAmt = contract.totalAmt
            if totalAmt > 0 and payment_total > 0:
                percentage = payment_total*100/totalAmt

            contract.update({
                'sale_total': sale_total,
                'invoice_total': invoice_total,
                'payment_total': payment_total,
                'percentage': percentage,
               
            })

    name = fields.Char('Order Reference', readonly=True, copy=False, default='New')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', default=lambda self: self.env.company.barter_warehouse_id, readonly=True, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True, index=True, default=lambda self: self.env.company.id)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    
    
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,default=lambda self: self.env.company.currency_id.id)
    user_id = fields.Many2one(
        'res.users', string='User', index=True, tracking=True, readonly=True,
        default=lambda self: self.env.user, check_company=True)
    
    start_date = fields.Datetime('Start Date', required=True, index=True, copy=False, default=fields.Datetime.now,\
        help="Contract's start date.")
    end_date = fields.Datetime('End Date', required=True, index=True, copy=False, default=fields.Datetime.now,\
        help="Contract's start date.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('canceled', 'Canceled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    notes = fields.Text('Terms and Conditions')

    order_ids = fields.One2many('sale.order', 'contract_id', string='Sale Orders',)
    invoice_ids = fields.One2many('account.move', 'contract_id', string='Invoices',)
 
    totalAmt = fields.Monetary(string='Contract\'s Amount', )
    sale_total = fields.Monetary(string='Sale Total Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    invoice_total = fields.Monetary(string='Invoice Total Amount', store=True, readonly=True, compute='_amount_all')
    payment_total = fields.Monetary(string='Payment Total', store=True, readonly=True, compute='_amount_all')
    percentage = fields.Float(string='Percentage of Performance', store=True, readonly=True, compute='_amount_all')

    contract_type =  fields.Selection([
        ('year', 'Year'),
        ('month', 'Month'),
        ('half_month', 'Half a month'),
        ('travel', 'Travel')], string='Type', )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'start_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['start_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract', sequence_date=seq_date) or '/'
        return super(SaleContract, self).create(vals)
    
    @api.depends('name', 'partner_id')
    def name_get(self):
        result = []
        for contract in self:
            name = contract.name
            if contract.partner_id:
                # str() функц нь coding: utf-8 гэж өгсөн ч алдаа заагаад байсан
                name = contract.name + u' - ' + contract.partner_id.name
            result.append((contract.id, name))
        return result


    def action_sent(self):
        self.write({'state': "sent"})
        return True

    def action_cancel(self):
        self.write({'state': "canceled"})
        return True

    def action_set_draft(self):
        self.write({'state': "draft"})
        return True
    
    def action_approve(self):
        self.write({'state': "approved"})
        return True

    def unlink(self):
        for contract in self:
            if contract.state in ['canceled', 'approved']:
                raise UserError(_('You cannot delete a approved or canceled contract.'))
            elif contract.order_ids:
                raise UserError(_('The contract selected for sale cannot be delete'))
            elif contract.invoice_ids:
                raise UserError(_('The contract selected in the invoice cannot be delete'))
        return super(SaleContract, self).unlink()