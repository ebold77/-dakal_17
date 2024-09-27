# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockTransitOrderLine(models.Model):
    _name = 'stock.transit.order.line'
    _description = 'Replenishment Order Line'
    _order = 'id'

    @api.depends('product_id')
    def _get_qty(self):
        move_qty = 0
        qty = 0
        for line in self:
            if line.product_id:
                warehouse = line.transit_order_id.supply_warehouse_id
                warehouse1 = line.transit_order_id.warehouse_id
                if not warehouse:
                    raise UserError(_('Warning!\nYou must select supply warehouse before add order line!'))
                product = line.product_id
                
                if line.transit_order_id.supply_picking_type_id.default_location_src_id:
                    locations = [line.transit_order_id.supply_picking_type_id.default_location_src_id]
                else:
                    locations = self.env['stock.location'].search([('usage', '=', 'internal'), ('location_id', 'child_of', [warehouse.view_location_id.id])])
                loc_ids = [loc.id for loc in locations or []]
              
                line.availability = product.with_context({'location': warehouse.lot_stock_id.id, 'to_date': line.transit_order_id.date_order}).qty_available#get_qty_availability(loc_ids, line.transit_order_id.date_order)
                line.balance = product.with_context({'location': warehouse1.lot_stock_id.id, 'to_date': line.transit_order_id.date_order}).qty_available
                line.product_uom_id = product.uom_id.id
                line.name = product.name
            else:
                line.availability = 0
                line.balance = 0

    # @api.model
    def _get_availability(self):
        self.availability = self.product_qty

    name = fields.Text('Description', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'stock.transit.order.line'),
        required=True)
    date_planned = fields.Datetime(
        'Scheduled Date', default=fields.Datetime.now,
        required=True, index=True, )
    product_id = fields.Many2one(
        'product.product', 'Product',
        readonly=True, required=True,
        domain=[('type', '!=', 'service')])
    box_qty = fields.Float(
        'Box Quantity',
        digits='Product Unit of Measure',
        readonly=True, required=True)
    product_qty = fields.Float(
        'Quantity',
        digits='Product Unit of Measure',
        readonly=True, required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        readonly=True, required=True)
    state = fields.Selection(related="transit_order_id.state", store=True, string='Status', default='draft', copy=False, required=True)
    transit_order_id = fields.Many2one(
        'stock.transit.order', string='Parent Transit Order', ondelete='cascade')
    balance = fields.Float(compute='_get_qty', string='Balance Qty', store=True)
    availability = fields.Float(compute='_get_qty', string='Available Qty', store=True)
    price_unit = fields.Float(compute='_get_unit_cost', string='Price Unit', store=True)
    sub_total = fields.Float(compute='_compute_amount', string='Sub Total', readonly=True)
    route_id = fields.Many2one('stock.location.route', string='Route', domain=[
        ('sale_selectable', '=', True)])
    supply_warehouse_id = fields.Many2one('stock.warehouse', related='transit_order_id.supply_warehouse_id', store=True, readonly=True, search='_search_supply_warehouse_id', string='Supply Warehouse')
    warehouse_id = fields.Many2one('stock.warehouse', related='transit_order_id.warehouse_id', store=True, readonly=True, search='_search_warehouse_id', string='Receive Warehouse')
    date_order = fields.Datetime(related='transit_order_id.date_order', store=True, readonly=True, string='Date Order')
   
    @api.model
    def search(self, args, offset=0, limit=0, order=None, count=False):
        args = list(args)
        user = self.env['res.users'].browse(self._uid)
        for index in range(len(args)):
            if (type(args[index]) == list):
                if args[index][2]:
                    if args[index][2] == 'ODERP_WAREHOUSE':
                        args[index] = (args[index][0], args[index][1], user.allowed_warehouse_ids.ids)
        return super(StockTransitOrderLine, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env['res.users'].browse(self._uid)
        domain = list(domain)
        for index in range(len(domain)):
            if (type(domain[index]) == list):
                if domain[index][2]:
                    if domain[index][2] == 'ODERP_WAREHOUSE':
                        domain[index] = (domain[index][0], domain[index][1], user.allowed_warehouse_ids.ids)
        return super(StockTransitOrderLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                         orderby=orderby, lazy=lazy)

    def _search_supply_warehouse_id(self, operator, value):
        res = []
        if value:
            res = self.env['stock.transit.order.line'].search(['|', ('transit_order_id.supply_warehouse_id.name', 'ilike', value), ('transit_order_id.supply_warehouse_id.code', 'ilike', value)])
        return [('id', operator, res)]
    
    def _search_warehouse_id(self, operator, value):
        res = []
        if value:
            res = self.env['stock.transit.order.line'].search(['|', ('transit_order_id.warehouse_id.name', 'ilike', value), ('transit_order_id.warehouse_id.code', 'ilike', value)])
        return [('id', operator, res)]
        
    # @api.onchange('supply_warehouse_id', 'warehouse_id', 'configure_allowed_product_on_wh')
    # def set_domain_for_product(self):
    #     # Компанийн тохиргоонд АГУУЛАХАД БАРАА ТОХИРУУЛАХ чеклэгдсэн бол Нийлүүлэх/Хүргэх агуулахуудын барааны давхцлаар домайндав.
    #     if self.env.company.configure_allowed_product_on_wh:
    #         domain = {}
             
    #         if self.supply_warehouse_id and self.warehouse_id and self.supply_warehouse_id.wh_allowed_product_ids and self.warehouse_id.wh_allowed_product_ids:
    #             intersection = list(set(self.supply_warehouse_id.wh_allowed_product_ids) & set(self.warehouse_id.wh_allowed_product_ids))
    #             domain['product_id'] = [('id', 'in', [pro.id for pro in intersection])]
    #         else:
    #             domain['product_id'] = []
    #         return {'domain': domain}

    # def _compute_configure_allowed_product_on_wh(self):
    #     for obj in self:
    #         obj.configure_allowed_product_on_wh = obj.company_id.sudo().configure_allowed_product_on_wh if obj.company_id else self.env.company.sudo().configure_allowed_product_on_wh

    def _prepare_stock_moves(self, picking, location_id, location_dest_id, warehouse, picking_type_id ):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'date': self.transit_order_id.date_order,
            'date_deadline': self.date_planned,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'picking_id': picking.id,
            'partner_id': False,
            'state': 'draft',
            'company_id': self.transit_order_id.company_id.id,
            'price_unit': self.price_unit,
            'picking_type_id': picking_type_id,
            'group_id': self.transit_order_id.procurement_group_id.id,
            'origin': self.transit_order_id.name,
            'route_ids': warehouse.in_type_id.warehouse_id and [(6, 0, [x.id for x in warehouse.in_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': warehouse.id,
        }
        res.append(template)
        return res

    def _create_stock_moves(self, picking, type, warehouse, location_id = False, location_dest_id = False):
        print('picking, type, warehouse, location_id = False, location_dest_id = False', picking, type, warehouse, location_id, location_dest_id)
        '''Нөхөн дүүргэлтийн гарах, ирэх барааны stock.move үүсгэнэ'''
        moves = self.env['stock.move']
        for line in self:
            if type == 'in' and not location_dest_id and not location_dest_id:
                location_id = self.transit_order_id.company_id.internal_transit_location_id.id
                location_dest_id = self.transit_order_id.receive_picking_type_id.default_location_dest_id.id if self.transit_order_id.receive_picking_type_id and self.transit_order_id.receive_picking_type_id.default_location_dest_id else self.transit_order_id.warehouse_id.in_type_id.default_location_dest_id.id
                warehouse = self.transit_order_id.warehouse_id
                picking_type_id = self.transit_order_id.warehouse_id.in_type_id.id
            elif type != 'in' and not location_dest_id and not location_dest_id:
                location_id = self.transit_order_id.supply_picking_type_id.default_location_src_id.id if self.transit_order_id.supply_picking_type_id and self.transit_order_id.supply_picking_type_id.default_location_src_id else self.transit_order_id.supply_warehouse_id.out_type_id.default_location_src_id.id
                location_dest_id = self.transit_order_id.company_id.internal_transit_location_id.id
                warehouse = self.transit_order_id.supply_warehouse_id
                picking_type_id = self.transit_order_id.supply_picking_type_id.id if self.transit_order_id.supply_picking_type_id else self.transit_order_id.warehouse_id.out_type_id.id
            for val in line._prepare_stock_moves(picking, location_id, location_dest_id, warehouse, picking.picking_type_id.id):
                moves.create(val)
        return True

    @api.onchange('product_id', 'product_qty', 'product_uom_id')
    def onchange_product_id(self):
        if not self.product_id:
            self.product_uom_id = False
            self.name = False
            self.product_qty = False
        else:
            product = self.product_id
            self.product_uom_id = product.uom_id.id
            self.name = product.name
            self.price_unit = product.standard_price
    
    @api.onchange('box_qty')
    def onchange_box_qty(self):
       
        self.product_qty = self.box_qty * self.product_id.box_qty

    @api.onchange('product_id', 'product_qty')
    def onchange_product_qty(self):

        if self.product_qty > 0:
            self.box_qty = self.product_qty/self.product_id.box_qty

    @api.depends('product_id')
    def _get_unit_cost(self):
        for line in self:
            unit_cost = line.product_id.standard_price
            line.price_unit = unit_cost
            
    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        """
        Compute the sub_total of the Transit Order line.
        """
        for line in self:
            line.sub_total = line.price_unit * line.product_qty