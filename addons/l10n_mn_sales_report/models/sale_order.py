# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('date_order')
    def _compute_month_and_day(self):
        for order in self:
            if order.date_order:
                order.month = int(order.date_order.month)
                order.day = int(order.date_order.day)

    month = fields.Integer(compute=_compute_month_and_day, store=True)
    day = fields.Integer(compute=_compute_month_and_day, store=True)
