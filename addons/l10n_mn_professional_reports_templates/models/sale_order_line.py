# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_price_discount(self):
        res = {}
        discount = self.discount
        pricelist_discount = 0
        pricelist_id  = self.order_id.pricelist_id
        product_id = self.product_id
        base_price = self.price_unit
        # product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)

        # price, rule_id = self.order_id.pricelist_id.with_context(product_context)._get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        # print('price==========', price, rule_id)
    
        # pricelist_item = self.env['product.pricelist.item'].search([('id', '=', rule_id)])
        # print('pricelist_item==============', pricelist_item)
        # if pricelist_item:
        #     pricelist_discount = pricelist_item.price_discount
     
        # if pricelist_item.base_pricelist_id:
        #     price, rule_id = pricelist_item.base_pricelist_id.with_context(product_context)._get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)

        #     pricelist_item0 = self.env['product.pricelist.item'].search([('id', '=', rule_id),('pricelist_id','=', pricelist_id.id)])
        #     print('============pricelist_item0 ======== ',pricelist_item0.base_pricelist_id)
        #     if pricelist_item0.base_pricelist_id:
        #         base_pricelist_price, rule_id = pricelist_item0.base_pricelist_id.with_context(product_context)._get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        #         print('============base_price ======== ',base_price)
        #         base_price = base_pricelist_price
        #     else:
        #         base_price = pricelist_item0.fixed_price
            
        #     discount = pricelist_item0.price_discount
        # if pricelist_discount > 0:
        #     res = {'discount': str(round(discount, 0))+ ' + ' + str(round(pricelist_discount,0)),
        #             'base_price': base_price}
        # else:
        res = {'discount': str(round(discount, 0)),
                'base_price': base_price}
        print('===========re======', res)
        _logger.info(u'Product base_price:  %s ' % base_price)
        _logger.info(u'Rwes:  %s ' % res)
        return res