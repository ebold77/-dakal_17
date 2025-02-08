# -*- coding: utf-8 -*-
import re
from datetime import datetime
import logging

from odoo import api, fields, models, _
from odoo import exceptions
import odoo.addons.decimal_precision as dp  # @UnresolvedImport
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ############# Барааг тухайн үеийн үлдэгдэлтэй нь татах ################ 9672
    def get_online_product(self, product_id=None):
        products = []
        
        vals = {}
        _logger.info(u'Product ID:  %s. ' % product_id)
        category= self.env['product.category'].search([('id', '=', 2)])
        warehouse = self.env.user.company_id.online_warehouse_id
        pricelist = self.env.user.company_id.online_sale_pricelist_id
        if product_id:
            product = self.env['product.product'].search([('id', '=', product_id)])
            qty_available = product.with_context({'warehouse': warehouse.id}).qty_available
            # product_name_inter = ''
            lots= []
            if qty_available >0:
                categ_name = ''
                # if product.insurance_list_id:
                #         product_name_inter =  product.insurance_list_id.tbltNameInter 
                price = pricelist._get_product_price(
                        product=product,
                        quantity=1.0,
                        currency=self.company_id.currency_id,
                        date=self.date_order,
                    )
                if product.product_tmpl_id.categ_id:
                            for categ in product.product_tmpl_id.categ_id:
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
                        # 'manu_name': product.product_brand_ept_id.name,
                        'note': product.description,
                        'conditions_granting': product.conditions_granting,
                        'tbltManufacture': product.tbltManufacture,
                        'general_category_id': product.general_category_id.name
                        # 'product_name_inter': product_name_inter,
                        # 'maximum_qty_per_sale':product.maximum_qty_per_sale,
                        }
                
                product_lot_ids = self.env['stock.lot'].search([('product_id', '=', product.id),
                                ('expiration_date', '>=', datetime.today().strftime('%Y-%m-%d 23:23:59')),
                                ])
                for lot  in product_lot_ids:
                    lot_item = {}
                    qty_available = product.with_context({'warehouse': warehouse.id, 'lot_id': lot.id}).qty_available
                    if qty_available > 0:
                        lot_item['name'] = lot.name
                        lot_item['quantity'] = qty_available
                        lot_item['expiration_date'] = lot.expiration_date,
                        lots.append(lot_item)
              
                vals['lots'] = lots
                products.append(vals)
        else:
            for sub_categ in category.search([('id', 'child_of', category.ids)]):
                for product in self.env['product.product'].search([('categ_id', 'in', sub_categ.ids)]):
                    qty_available = product.with_context({'warehouse': warehouse.id}).qty_available
                    # product_name_inter = ''
                    categ_name = ''
                    lots= []
                    if qty_available >0:
                        
                        # if product.insurance_list_id:
                        #     product_name_inter =  product.insurance_list_id.tbltNameInter 
                        
                        price = pricelist._get_product_price(
                                product= product,
                                quantity=1.0,
                                currency=self.company_id.currency_id,
                                date=self.date_order,
                            )
                        if product.product_tmpl_id.categ_id:
                            for categ in product.product_tmpl_id.categ_id:
                                categ_name = categ.name
                        
                        vals={'product_id': product.id,
                                'bar_code': product.barcode,
                                'category': categ_name,
                                'product_name': product.product_tmpl_id.name,
                                'unit_name': product.uom_id.name,
                                'uldegdel_qty': qty_available,
                                'sale_price': price,
                                # 'manu_name': product.product_brand_ept_id.name,
                                'note': product.description,
                                'conditions_granting': product.conditions_granting,
                                'tbltManufacture': product.tbltManufacture,
                                'general_category_id': product.general_category_id.name
                                # 'product_name_inter': product_name_inter,
                                # 'maximum_qty_per_sale':product.maximum_qty_per_sale,
                                # 'discounted_price':discounted_price,
                                }
                        _logger.info(u'Categ Name:  %s ' % categ_name)
                        _logger.info(u'Product Name:  %s ' % product.product_tmpl_id.name)
                        product_lot_ids = self.env['stock.lot'].search([('product_id', '=', product.id),
                                ('expiration_date', '>=', datetime.today().strftime('%Y-%m-%d 23:23:59')),
                                ])
                        for lot  in product_lot_ids:
                            lot_item = {}
                            qty_available = product.with_context({'warehouse': warehouse.id, 'lot_id': lot.id}).qty_available
                            if qty_available > 0:
                                lot_item['id'] = lot.id
                                lot_item['name'] = lot.name
                                lot_item['quantity'] = qty_available
                                lot_item['expiration_date'] = lot.expiration_date,
                                lots.append(lot_item)
                    
                        vals['lots'] = lots
                        products.append(vals)
       
        return products

    def get_online_product_datas(self):
        data = {}
        
        lots= []
        product_lot_ids = self.env['stock.lot'].search([('product_id', '=', self.id),
                                ('expiration_date', '>=', datetime.today().strftime('%Y-%m-%d 23:23:59')),
                                ])
       
        qty_available_all = self.with_context({'warehouse': warehouse_id}).qty_available
        for lot  in product_lot_ids:
            lot_item = {}
            qty_available = self.with_context({'warehouse': warehouse_id, 'lot_id': lot.id}).qty_available
            if qty_available > 0:
                lot_item['id'] = lot.id
                lot_item['name'] = lot.name
                lot_item['quantity'] = qty_available
                lot_item['expiration_date'] = lot.expiration_date,
                lots.append(lot_item)
        data['product_id'] = self.id
        data['qty_available_all'] = qty_available_all
        data['lots'] = lots

       
        return data