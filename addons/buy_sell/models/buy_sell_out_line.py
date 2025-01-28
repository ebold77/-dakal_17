# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.tools.float_utils import float_round


class BuySellOutLine(models.Model):
    _name = "buy.sell.out.line"
    _description = "Buy and Sell Out Line"
    _order = 'order_id, sequence, id'
    
    
    order_id = fields.Many2one('buy.sell.order', string='Order Reference', index=True, required=True, ondelete='cascade')
    
    sequence = fields.Integer(string='Sequence', default=10)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True)
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    bs_price = fields.Float(string='Buy and Sell Price', required=True, digits='Product Price')
    list_price = fields.Float(string='List Price', required=True, digits='Product Price', readonly=True)
    pricelist_discount = fields.Float(string='PriceList Discount', required=True, digits='Discount', readonly=True)
    stock_available_qty = fields.Float(string='stock_available_qty', required=True, digits='Product', readonly=True)
    month_average_amount = fields.Float(string='Month average sale amount', required=True, digits='Product', readonly=True)
    bs_price_total = fields.Float(string='Buy and Sell Total Price', store=True, readonly=True)
    list_price_total = fields.Float(string='Total Price', store=True, readonly=True)
    discount_total = fields.Float(string='Discount Total', store=True, readonly=True)
    company_id = fields.Many2one('res.company', readonly=True, default=lambda self: self.env.company)
    
    @api.onchange('bs_price')
    def onchange_bs_price(self):
        if self.product_qty > 0:
            self.bs_price_total = self.bs_price * self.product_qty
            
    @api.onchange('product_qty')
    def onchange_product_qty(self):
        
        if not self.product_id:
            return
        
        self.bs_price_total = self.bs_price * self.product_qty
        pricelist = self.company_id.base_pricelist_id
        list_price = pricelist._get_product_price(self.product_id , 1, self.order_id.partner_id)
        list_price_total = list_price * self.product_qty
        self.discount_total = (list_price_total*self.pricelist_discount)/100
        
        sale_pricelist = self.company_id.sale_pricelist_id
        sale_price = sale_pricelist._get_product_price(self.product_id , 1, self.order_id.partner_id)
        self.list_price_total = sale_price* self.product_qty
        
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        pricelist = self.company_id.base_pricelist_id
        sale_pricelist = self.company_id.sale_pricelist_id
        
        # Reset date, price and quantity since _onchange_quantity will provide default values
        list_price = pricelist._get_product_price(self.product_id , 1, self.order_id.partner_id)
        
        self.list_price = list_price
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        # 'net_on_hand': obj.with_context({'warehouse': warehouse, 'to_date': end_date}).qty_available
        self.stock_available_qty = self._get_stock_available_qty(self.product_id.id, self.order_id.warehouse_id.id)
        self.month_average_amount =  self.get_month_average_amount(self.product_id.id)  
        base_price = self._get_bs_price(self.product_id, self.order_id.pricelist_id.id)['price']
        sale_price = self._get_bs_price(self.product_id, sale_pricelist.id)['price']
        print('sa', sale_price, 'base price===', base_price)
        discount = 100 - sale_price*100/base_price
        self.bs_price  = base_price
        self.pricelist_discount = discount
        
    
    def _get_bs_price(self, product_id, pricelist_id):
        
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        # price_dict = pricelist._get_product_price(product_id, 1, self.order_id.partner_id)
        price_dict = pricelist._get_product_price(
                    product=self.product_id,
                    quantity=1.0,
                    currency=self.company_id.currency_id,
                    date=self.order_id.date_order,
                   )
        print('price_dict====>>', price_dict)
        discount = 100 - (price_dict*100/self.product_id.lst_price)
        res={
            'price' : price_dict,
            'discount': discount
            }
        return res                 
                                    
                                    
    def _get_stock_available_qty(self, product_id, warehouse_id):
        product =  self.env['product.product'].browse(product_id)
        print('product.-------->>', product)
        res = product._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        print('res=========================>>>>>>>>>>>>>>', res)
        qty_available = res[product.id]['qty_available']
        return qty_available
    
    def get_month_average_amount(self, product_id):
        product =  self.env['product.product'].browse(product_id)
        res = product._compute_sales_count()
        if res:
            return res[product.id]/12
    

        
                                    
                                    
                                    
                                    
                                    
                                    
                                    