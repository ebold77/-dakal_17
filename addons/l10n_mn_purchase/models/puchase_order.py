# -*- coding: utf-8 -*-
################################################################################
#
#    Dakalpharm. Ltd.
#
#    Copyright (C) 2024-TODAY Dakalpham.
#    Author: Enkhbold (ebold77@gmail.com)
#
################################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """ Class for inherited model purchase order line. Contains a field for line
        qty_available and sale's price.
    """

    _inherit = 'purchase.order.line'

    qty_available = fields.Integer(string='Qty Available', help='Qty Available')
    sale_price = fields.Float(string='Sale Price', help='Sale Price')
    is_expensive = fields.Boolean(string='Is Expensive', default=False)

    def _get_bs_price(self, product_id, pricelist_id):
        
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        price_dict = pricelist._get_product_price(
                    product=self.product_id,
                    quantity=1.0,
                    currency=self.company_id.currency_id,
                    date=self.order_id.date_order,
                   )
        
        discount = 100 - (price_dict*100/self.product_id.lst_price)
        res={
            'price' : price_dict,
            'discount': discount
            }
        return res   

    @api.onchange('product_id')
    def onchange_product_id(self):
        line = super(PurchaseOrderLine, self).onchange_product_id()
        sale_pricelist = self.company_id.sale_pricelist_id
        
        qty_available = self.product_id.with_context({'warehouse': self.order_id.picking_type_id.warehouse_id.id}).qty_available

        
        self.write({'qty_available': qty_available})
        if self.product_id:
            sale_price = self._get_bs_price(self.product_id, sale_pricelist.id)['price']
            if sale_price < self.price_unit:
                self.write({'is_expensive': True})
            self.write({'sale_price': sale_price})
          