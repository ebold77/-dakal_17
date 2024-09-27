# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = "sale.order"

              
    driver_id = fields.Many2one('hr.employee', string='Driver', store=True, readonly=True)
    
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
                           'driver_id': self.driver_id.id
                           })

        return invoice_vals