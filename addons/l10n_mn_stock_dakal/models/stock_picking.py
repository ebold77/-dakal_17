# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_note = fields.Html(related="sale_id.note", string="Sales Note", store=True, readonly=False)
    driver_id =  fields.Many2one('hr.employee', string="Driver")

    def write(self, vals):
        res = super().write(vals)
        if vals.get('driver_id'):
            sale_order =  self.sale_id
            sale_order.write({'driver_id': vals.get('driver_id')})
            for invoice in sale_order.invoice_ids:
                invoice.write({'driver_id': vals.get('driver_id')})
        return res

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.sale_id:
            picking = self.env['stock.picking'].search([('sale_id', '=', self.sale_id.id)])
            if picking:
                for pick in picking:
                    pick.write({'driver_id': self.driver_id.id})
        if self.transit_order_id:
            picking = self.env['stock.picking'].search([('transit_order_id', '=', self.transit_order_id.id)])
            if picking:
                for pick in picking:
                    pick.write({'driver_id': self.driver_id.id})