from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_discount': amount_discount,
                'amount_total': amount_untaxed + amount_tax,
            })
            
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_amount_all')
    partner_employee_phone = fields.Char(string='Employee Phone')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse' )
    is_contract = fields.Selection([('no_contract', 'No Contract'),
                               ('contract', 'Contract'),
                               ('loan_contract', 'Loan Contract')], string='Is Contract', default='no_contract')

       
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.is_contract = self.partner_id.is_contract
        self.partner_employee_phone = self.partner_id.mobile

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({'warehouse_id': self.warehouse_id.id,
                            'pricelist_id': self.pricelist_id.id,
                            'invoice_payment_term_id': self.payment_term_id.id,
                            })

        return invoice_vals