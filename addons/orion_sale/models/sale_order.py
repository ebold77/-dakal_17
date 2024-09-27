# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError  # @UnresolvedImport

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"


    ############# Барааг тухайн үеийн үлдэгдэлтэй нь татах ################ 9672
    def get_product(self, product_id=None):
        products = []
        vals = {}
        _logger.info(u'Product ID:  %s. ' % product_id)
        category= self.env['product.category'].search([('id', '=', 2)])
        warehouse = self.env.user.company_id.orion_warehouse_id
        pricelist = self.env.user.company_id.orion_base_pricelist_id
        discounted_pricelist = self.env.user.company_id.orion_sale_pricelist_id
        if product_id:
            product = self.env['product.product'].search([('id', '=', product_id)])
            qty_available = product.with_context({'warehouse': warehouse.id}).qty_available
            product_name_inter = ''
            if qty_available >0:
                categ_name = ''
                if product.insurance_list_id:
                        product_name_inter =  product.insurance_list_id.tbltNameInter 
                price = pricelist._get_product_price(product, qty_available, 1)
                discounted_price = discounted_pricelist._get_product_price(product, qty_available, 1)
                if product.public_categ_ids:
                            for categ in product.public_categ_ids:
                                categ_name = categ.name
                _logger.info(u'Categ Name:  %s ' % categ_name)
                _logger.info(u'Product Name:  %s ' % product.product_tmpl_id.name)
                vals={'product_id': product.id,
                        'bar_code': product.barcode,
                        'category': categ_name,
                        'product_name': product.product_tmpl_id.name,
                        'unit_name': product.uom_id.name,
                        'uldegdel_qty': qty_available,
                        'sale_price': price,
                        'manu_name': product.product_brand_ept_id.name,
                        'note': product.description,
                        'product_name_inter': product_name_inter,
                        'maximum_qty_per_sale':product.maximum_qty_per_sale,
                        'discounted_price':discounted_price,
                        }
                products.append(vals)
        else:
            for sub_categ in category.search([('id', 'child_of', category.ids)]):
                for product in self.env['product.product'].search([('categ_id', 'in', sub_categ.ids)]):
                    qty_available = product.with_context({'warehouse': warehouse.id}).qty_available
                    product_name_inter = ''
                    categ_name = ''
                    if qty_available >0:
                        
                        # if product.insurance_list_id:
                        #     product_name_inter =  product.insurance_list_id.tbltNameInter 
                        
                        price = pricelist._get_product_price(product, qty_available, 1)
                        if product.public_categ_ids:
                            for categ in product.public_categ_ids:
                                categ_name = categ.name
                        discounted_price = discounted_pricelist._get_product_price(product, qty_available, 1)
                        vals={'product_id': product.id,
                                'bar_code': product.barcode,
                                'category': categ_name,
                                'product_name': product.product_tmpl_id.name,
                                'unit_name': product.uom_id.name,
                                'uldegdel_qty': qty_available,
                                'sale_price': price,
                                'manu_name': product.product_brand_ept_id.name,
                                'note': product.description,
                                'product_name_inter': product_name_inter,
                                'maximum_qty_per_sale':product.maximum_qty_per_sale,
                                'discounted_price':discounted_price,
                                }
                        _logger.info(u'Categ Name:  %s ' % categ_name)
                        _logger.info(u'Product Name:  %s ' % product.product_tmpl_id.name)
                        products.append(vals)
        print('products===================================>>\n')
        return products

    ############# Нэг харилцагч Регистрийн дугаараар Татах ################
    def get_partner(self, regno=None):
        res = {}
        error_msg = ''
        _logger.info(u' %s дугаар илгээсэн байна. ' % regno)
        try:
            if regno:
                partner_ids = self.env['res.partner'].search([('vat', '=', regno),('category_id', '=', 71)])
                if partner_ids:
                    for partner in partner_ids:
                        if partner.phone:
                            _logger.info(u'Харилцагчийн ID:  %s. ' % partner.id)
                            _logger.info(u'Харилцагчийн регистр:  %s. ' % partner.vat)
                            _logger.info(u'Харилцагчийн нэр:  %s. ' % partner.name)
                            _logger.info(u'Харилцагчийн Утас:  %s. ' % partner.phone)
                            res = {
                                'id': partner.id,
                                'name': partner.name,
                                'vat': partner.vat,
                                'phone': partner.phone,

                            }
            else:
                raise ValidationError(u'Регистрийн дугаар хоосон байна!')
        except Exception as e:
            error_msg += str(e)
            res = {
                    'error_msg': error_msg,
                    }
        return res

    ############# Борлуулалт үүсгэх ################
    def create_order(self, partner_id=None, paymentMethod='cash', note=None, items=None):
        res = {}
        error_msg = ''
        success = False
        # items = [{'product_id': 7102, 'qty':14}, {'product_id': 7101, 'qty':20}]
        # partner_id = self.get_partner(regno='6246923')  
        # print('partner_id===', partner_id['id'])
        order_vals = {
            'partner_id': partner_id,
            'warehouse_id': self.env.user.company_id.orion_warehouse_id.id,
            'pricelist_id': self.env.user.company_id.orion_sale_pricelist_id.id,
            'payment_term_id': 1,
            'website_id': 1,
            'state': 'draft',
            'note': note,
        }
        try:
            order_id = self.env['sale.order'].create(order_vals)
            if order_id:
                for item in items:
                    line_vals = {
                        'product_id': item['product_id'],
                        'product_uom_qty': item['qty'],
                        'order_id': order_id.id
                    }
                    line = self.env['sale.order.line'].create(line_vals)
                    line._onchange_discount()

                success = True
                res = {
                    'success': success,
                    'order_id': order_id.id,
                    'order_name': order_id.name,
                    'error_msg': error_msg,

                }
        except Exception as e:
            error_msg += str(e)
            res = {
                    'success': success,
                    'order_id': False,
                    'order_name': '',
                    'error_msg': error_msg,
                    }
        return res


