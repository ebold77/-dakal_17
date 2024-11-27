# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, time
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


class BuySellOrder(models.Model):
    _name = "buy.sell.order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Buy and Sell Order"
    _order = 'date_order desc, id desc'

    @api.depends('sell_order_line.bs_price_total', 'buy_order_line.bs_price_total')
    def _amount_all(self):
        for order in self:
            pro_loss_buy = pro_loss_sale = 0
            sales_amount = sales_amount_buy = 0
            amount_sell = amount_buy = 0
            for line in order.sell_order_line:
                amount_sell += line.bs_price_total
                sales_amount += line.list_price_total
            for line in order.buy_order_line:
                amount_buy += line.bs_price_total
                sales_amount_buy += line.list_price_total
            pro_loss_sale = amount_sell - sales_amount
            pro_loss_buy = sales_amount_buy - amount_buy
            order.update({
                'sell_total': order.currency_id.round(amount_sell),
                'buy_total': order.currency_id.round(amount_buy),
                'price_difference': amount_sell - amount_buy,
                'profit_loss_sale': order.currency_id.round(pro_loss_sale),
                'profit_loss_buy': order.currency_id.round(pro_loss_buy),
            })

    READONLY_STATES = {
        'sent': [('readonly', True)],
        'checked': [('readonly', True)],
        'approved': [('readonly', True)],
        'received': [('readonly', True)],
        'delivered': [('readonly', True)],
        'canceled': [('readonly', True)],
    }
    
    def print_report(self):
        return self.env.ref('buy_sell.action_report_buysaleorder').report_action(self)


    def _get_sale_tax(self):
        tax_id = self.env.company.account_sale_tax_id

        return tax_id.id
    
    def _get_purchase_tax(self):
        tax_id = self.env.company.account_purchase_tax_id

        return tax_id.id
    
    @api.depends('purchase_order_id')
    def _received(self):
        
        for order in self:
            if order.purchase_order_id:
                if order.purchase_order_id.state == 'purchase' and order.state == 'approved':
                    if order.purchase_order_id.is_shipped:
                        order.received = True
                        if order.state in ('approved',):
                            order.action_receive()
                    else:
                        order.received = False
                        return  order.received
                else:
                    order.received = False
                    return  order.received
            else:
                order.received = False
                return  order.received
    
    @api.depends('sale_order_id')
    def _delivered(self):
        for order in self:
            if order.sale_order_id:
                if order.sale_order_id.state == 'sale' and order.state == 'approved':
                    pick =  self.env['stock.picking'].search([('sale_id', '=', order.sale_order_id.id)])
                    if pick['state'] =='done':
                        order.delivered = True
                        if order.state in ('approved', 'received'):
                            order.action_deliver()
                    else:
                        order.delivered = False
                        return  order.delivered
                else:
                    order.delivered = False
                    return  order.delivered
            else:
                order.delivered = False
                return  order.delivered

    name = fields.Char('Order Reference', readonly=True, index=True, copy=False, default='New')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', default=lambda self: self.env.company.barter_warehouse_id, readonly=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True,  change_default=True, help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    pricelist_id = fields.Many2one('product.pricelist', string='PriceList', default=lambda self: self.env.company.barter_pricelist_id, readonly=True, required=True)
    sale_tax_id = fields.Many2one('account.tax', string='Sale\'s Taxes', domain=['|', ('active', '=', False), ('active', '=', True)], default = _get_sale_tax)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True,)
    date_order = fields.Datetime('Order Date', required=True, index=True, copy=False, default=fields.Datetime.now,\
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    origin = fields.Char('Source Document', copy=False,
        help="Reference of the document that generated this purchase order "
             "request (e.g. a sales order)")
    buy_sell_tax_id = fields.Many2one('account.tax', string='Purchase\'s Taxes', domain=['|', ('active', '=', False), ('active', '=', True)], default = _get_purchase_tax)
    purchase_order_id =fields.Many2one('purchase.order', string='Purchase Order', readonly=True,)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('checked', 'Checked'),
        ('approved', 'Approved'),
        ('received', 'Receive Done'),
        ('delivered', 'Delivery Done'),
        ('canceled', 'Canceled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    sell_order_line = fields.One2many('buy.sell.out.line', 'order_id', string='Out Order Lines', copy=True,)
    buy_order_line = fields.One2many('buy.sell.in.line', 'order_id', string='In Order Lines', copy=True,)
    notes = fields.Text('Terms and Conditions')
    sell_total = fields.Monetary(string='Sell Total Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    buy_total = fields.Monetary(string='Buy Total Amount', store=True, readonly=True, compute='_amount_all')
    price_difference = fields.Monetary(string='Price Difference', store=True, readonly=True, compute='_amount_all')
    user_id = fields.Many2one(
        'res.users', string='User', index=True, tracking=True, readonly=True,
        default=lambda self: self.env.user, check_company=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True, index=True, default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
        default=lambda self: self.env.company.currency_id.id)
    
    date_approve = fields.Date('Date Approved', readonly=True, help="Date on which sale purchase order has been approved", copy=False)
    validator_id = fields.Many2one('res.users', 'Validated by', readonly=True, copy=False)
    delivered = fields.Boolean('Delivered', readonly=True, compute='_delivered', help="It indicates that a sending of goods has been done", default=False)
    received = fields.Boolean('Received', readonly=True, compute='_received', help="It indicates that a reception of goods has been done", default=False)
    profit_loss_buy = fields.Monetary(string='Profit and Loss Sale', store=True, readonly=True, compute='_amount_all')
    profit_loss_sale = fields.Monetary(string='Profit and Loss Buy', store=True, readonly=True, compute='_amount_all')
    
    @api.model_create_multi
    def create(self, vals):
        if self.name == 'New':
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('buy.sell.order', sequence_date=seq_date) or '/'
        return super(BuySellOrder, self).create(vals)
    
    def action_sent(self):
        self.write({'state': "sent"})
        return True

    def unlink(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_("You cannot delete an barter which has been draft once."))
        return super(BuySellOrder, self).unlink()
    
    def action_cancel(self):
        sale_ok = True
        purchase_ok = True
        if self.sale_order_id:
            if self.sale_order_id.state =='draft':
                self.sale_order_id.unlink()
                sale_ok = False
            elif self.sale_order_id.state =='cancel':
                sale_ok = False
            else:
                raise ValidationError(_('This order cannot be canceled as there is a related sales order'))
        else:
            sale_ok = False
        if self.purchase_order_id:
        
            if self.purchase_order_id.state =='draft':
                self.purchase_order_id.unlink()
                purchase_ok = False
            elif self.purchase_order_id.state =='cancel':
                purchase_ok = False
            else:
                raise ValidationError(_('This order cannot be canceled as there is a related purchases order'))
        else:
            purchase_ok = False
        if sale_ok == False and purchase_ok ==False:
            self.write({'state': "canceled"})
        return True
    
    def action_set_draft(self):
        self.write({'state': "draft"})
        return True
    
    def action_check(self):
        self.write({'state': "checked"})
        return True
    
    def action_approve(self):
        picking_type = self.env['stock.picking.type'].search([('warehouse_id','=', self.warehouse_id.id),('code','=','incoming')])
        vals = {
            'partner_id': self.partner_id.id,
            'date_order': self.date_order,
            'picking_type_id':picking_type.id,
            'purchase_type':'barter',
            }
        purchase_id = self.env['purchase.order'].create(vals)
        for line in self.buy_order_line:
            line_vals = {
                'product_id':line.product_id.id,
                'product_qty': line.product_qty,
                'price_unit':line.bs_price,
                'order_id':purchase_id.id,
                'taxes_id': [(6, 0, [self.buy_sell_tax_id.id])]
                }
            purchase_line = self.env['purchase.order.line'].create(line_vals)
        self.write({'state': "approved",
                    'purchase_order_id': purchase_id,
                    'validator_id': self.env.user.id,
                    'date_approve': datetime.now()
                    })
        
        source_id = self.env['utm.source'].search([('name','=', 'barter')])
        if not source_id:
            source_id = self.env['utm.source'].create({'name': 'barter'})
        vals = {
            'partner_id': self.partner_id.id,
            'date_order': self.date_order,
            'pricelist_id': self.pricelist_id.id,
            'warehouse_id': self.warehouse_id.id,
#             'picking_type_id':picking_type.id,
            'source_id':source_id.id
            }
        sale_id = self.env['sale.order'].create(vals)
        for line in self.sell_order_line:
            line_vals = {
                'product_id':line.product_id.id,
                'product_uom_qty': line.product_qty,
                'price_unit':line.bs_price,
                'order_id':sale_id.id,
                'tax_id': [(6, 0, [self.sale_tax_id.id])]
                }
            sale_line = self.env['sale.order.line'].create(line_vals)
            
        self.write({'sale_order_id': sale_id})
        
        return True
    
    def action_deliver(self):
        if self and self.delivered:
            self.env.cr.execute("UPDATE buy_sell_order SET state = 'delivered' WHERE id = %s", (self.id,))
    
    def action_receive(self):
        if self and self.received:
            #self.state = 'received'
            self.env.cr.execute("UPDATE buy_sell_order SET state = 'received' WHERE id = %s", (self.id,))
            
    
    
