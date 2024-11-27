

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp

from odoo.exceptions import UserError, ValidationError

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_id = fields.Many2one('sale.contract', string='Sale\'s Contract',)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
       
        contract_id = self.env['sale.contract'].search([
                    ('partner_id', '=', self.partner_id.id),
                    ('start_date', '<=', self.date_order),
                    ('end_date', '>=', self.date_order)
                ])
        if contract_id:
            
            self.contract_id = contract_id
        else:
            self.contract_id = False 

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        contract_type = self.contract_id.contract_type
        
        for line in self.order_line:
            if line.product_id.is_rewards and contract_type == 'travel':
                raise ValidationError(_("You cannot sell [%s] %s product to customers with a travel contract")%(line.product_id.default_code, line.product_id.name))
        return res

    def _prepare_invoice(self):
        invoice_vals= super(SaleOrder, self)._prepare_invoice()

        if self.contract_id:
            invoice_vals['contract_id'] = self.contract_id.id
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    @api.onchange("product_id")
    def product_id_change(self):
        res = super(SaleOrderLine, self)._onchange_product_id_warning() or {}
        contract_type = self.order_id.contract_id.contract_type

        if self.product_id.is_rewards and contract_type == 'travel':
            raise ValidationError(_("You cannot sell this product to customers with a travel contract"))
        return res