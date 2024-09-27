# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError, ValidationError


class StockTransitOrder(models.Model):
    _name = 'stock.transit.order'
    _description = 'Replenishment Order'
    _inherit = ['mail.thread']
    _order = 'date_order desc'

    STATE_SELECTION = [('draft', 'Draft'),
                       ('approved', 'Approved'),
                       ('done', 'Done'),
                       ('cancel', 'Cancelled'), ]

    def _domain_warehouses(self):
        return [ '|', ('company_id', '=', False),
                ('company_id', 'in', (self.company_id.ids or self.env.company.ids))]

    def _compute_is_stock_manager(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            self.is_stock_manager = True
        else:
            self.is_stock_manager = False

    def compute_transfer_status(self):
        for obj in self:
            is_supplied = is_received = False
            if obj.picking_ids:
                for pick in obj.picking_ids:
                    if pick.picking_type_id.code == 'outgoing':
                        is_supplied = True if pick.state == 'done' else False
                    if pick.picking_type_id.code == 'incoming':
                        is_received = True if pick.state == 'done' else False
            obj.is_supplied = is_supplied
            obj.is_received = is_received
            if obj.is_received and obj.is_supplied:
                obj.check_done()

    @api.depends('picking_ids')
    def _count_all(self):
        shipment_count = 0
        receipt_count = 0
        for pick in self.picking_ids:
           
            if pick.picking_type_id.code == 'IN':
                receipt_count += 1
            elif pick.picking_type_id.code == 'OUT':
                shipment_count += 1
        self.shipment_count = shipment_count
        self.receipt_count = receipt_count


    name = fields.Char('Name', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Receive Warehouse')
    supply_warehouse_id = fields.Many2one('stock.warehouse', string='Supply Warehouse', domain=_domain_warehouses)
    user_id = fields.Many2one('res.users', string='Responsible', required=False, default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, domain="[('parent_id', '=', company_id)]")
    date_order = fields.Datetime(string='Date Order', default=fields.Datetime.now)
    receive_date = fields.Datetime(string='Receive Date', default=fields.Datetime.now)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    route_id = fields.Many2one('stock.route', string="Preferred Route")
    receive_picking_type_id = fields.Many2one('stock.picking.type', string="Receive Location",
                                              domain="[('code', '=', 'incoming'),('warehouse_id','=',warehouse_id)]")
    supply_picking_type_id = fields.Many2one('stock.picking.type', string="Supply Location",
                                             domain="[('code', '=', 'outgoing'),('warehouse_id','=',supply_warehouse_id)]")
    state = fields.Selection(STATE_SELECTION, default='draft')
    procurement_group_id = fields.Many2one('procurement.group', string='Procurement group', copy=False)
    note = fields.Text(string='Note')
    is_supplied = fields.Boolean('Supplied', default=False, compute='compute_transfer_status', search='_search_is_supplied')
    is_received = fields.Boolean('Received', default=False, compute='compute_transfer_status', search='_search_is_received')
    move_assign_date = fields.Datetime(string='Move assign date', default=False)
    is_stock_manager = fields.Boolean(compute='_compute_is_stock_manager')
    picking_ids = fields.One2many('stock.picking', 'transit_order_id', 'Picking List', readonly=True)
    order_line_ids = fields.One2many('stock.transit.order.line', 'transit_order_id', 'Order Lines')
    product_id = fields.Many2one('product.product', related='order_line_ids.product_id', string='Product')
    shipment_count = fields.Integer(string='Outgoing Shipments', store=True, readonly=True, compute='_count_all')
    receipt_count = fields.Integer(string='Incoming Shipments', store=True, readonly=True, compute='_count_all')
    driver_id =  fields.Many2one('hr.employee', string="Driver", required=True)


    def approve(self):
        #########################################################################################
        #   Нийлүүлэх агуулах болон хүлээн авах агуулахуудын дундын байрлалд хүлээн аваагүй     #
        #   бараа байгаа эсэхийг шалгана.                                                       #    
        #########################################################################################
        print('self.route_id.rule_ids[0].-------------->>', self.route_id.rule_ids[0].name)
        transit_location = self.route_id.rule_ids[0].location_dest_id
        prod_obj = self.env['product.product']
        def _product_get(d):
                qty = d.get('qty', 0)      
                return (d['name'], qty)
        product_ids = prod_obj._search_qty_available_new('>', 0)
        product_dict = {}
        product_list = []

        if product_ids:
            for product in prod_obj.search([('id', 'in', product_ids)]):
                qty_available = product.with_context({'location': transit_location.id,}).qty_available
                if qty_available > 0:
                    mydict = {
                      'name': '[%s] %s' %(product.default_code,product.name),
                      'qty': qty_available,
                      }
                    temp = _product_get(mydict)
                    product_list.append(temp)
                    product_dict = dict(product_list)
            if product_dict:
                
                raise UserError(u'Нийлүүлэх агуулах болон хүлээн авах агуулахуудын дундын байрлалд хүлээн аваагүй \n'+
                    '%s бараа байна. \n Тухайн барааг хүлээн авсаны дараа Нөхөн дүүргэлт хийх боломжтой.' %product_dict +
                    '\n Хүлээн авах агуулахын нярав барааг хүлээн авах эсвэл \n Нийлүүлэх агуулахын нярав буцаалт хийх шаардлагатай.')
        for transit in self:
            # Захиалгын мөр байгаа эсэхийн шалгаж байна
            if transit.order_line_ids:
                if not transit.name:
                    transit.name = self.env['ir.sequence'].get('stock.transit.order')
            else:
                raise UserError(_('Order line is not created'))
        self._create_picking()
        self.state = 'approved'
    
    def action_cancel_draft(self):
        ''' Цуцласан захиалгыг ноорог болгох
        '''
        for order in self:
            order.write({'state': 'draft',
                         'is_supplied': False,
                         'is_received': False,
                         'move_assign_date': False,
                         # 'check_sequence': False,
                         # 'workflow_id': False
                         })
        return True

    def action_cancel(self):
        ''' Нөхөн дүүргэлтийн захиалгыг цуцална. Агуулахын хөдөлгөөн үүссэн бөгөөд шилжсэн тохиолдолд цуцлагдахгүй. Шилжээгүй тохиолдолд үүссэн агуулахын хөдөлгөөнүүдийг
            устгаж нөхөн дүүргэлтийн захиалгыг цуцалсан төлөвт оруулна.
        '''
        for order in self:
            for pick in order.picking_ids:
                if pick.picking_type_id.code == 'incoming':
                    if pick.state in ('done'):
                        raise UserError(
                            _(
                                'Cannot cancel replenishment order !\n Because picking state is Done of reception attached to this replenishment order.'))
                    else:
                        pick.action_cancel()
                        pick.unlink()
                else:
                    if pick.state in ('done'):
                        raise UserError(_(
                            'Cannot cancel replenishment order ! \n Because picking state is Done shipping document attached to this replenishment order.'))
                    else:
                        pick.action_cancel()
                        pick.unlink()
            order.write({'state': 'cancel', 'move_assign_date': False})
        return True

    def check_done(self):
        ''' Бараа хүлээн авах захиалгыг дуусгах үед
            нөхөн дүүргэлтийн захиалгыг дууссан төлөвт шилжүүлнэ.
        '''
        ok = True
        for picking in self.picking_ids:
            if picking.picking_type_id.code == 'incoming' and picking.state not in ('done'):
                ok = False
            elif picking.picking_type_id.code == 'outgoing' and picking.state not in ('done'):
                ok = False
        if ok:
            message = _("Replenishment receivement has been complete.")
            self.message_post(body=message)
            self.write({'state': 'done'})
        return ok

    @api.model
    def _prepare_picking(self, location_id, location_dest_id, receive_picking_type_id):
        if not self.procurement_group_id:
            self.procurement_group_id = self.procurement_group_id.create({
                'name': self.name,
            })
        return {
            'picking_type_id': receive_picking_type_id,
            'transit_order_id': self.id,
            'date': self.receive_date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'driver_id': self.driver_id.id,
        }

    def _create_picking(self):
        """Гарах Ирэх барааны хүргэлтийн захиалга үүсгэх функц"""
        StockPicking = self.env['stock.picking']
        for order in self:
            
            location_src_id = False
            location_id = False
            if any([ptype in ['product', 'consu'] for ptype in order.order_line_ids.mapped('product_id.type')]):
                in_pickings = order.picking_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel') and x.picking_type_id.code == 'incoming')
                if not in_pickings:
                    if self.warehouse_id.reception_steps == 'two_steps':
                        int_type_id = self.warehouse_id.int_type_id.id

                        for rule in self.route_id.rule_ids:
                            if rule.picking_type_id.id == self.receive_picking_type_id.id:
                                location_src_id = rule.location_src_id.id
                        in_location_id = location_src_id
                        in_location_dest_id = self.receive_picking_type_id.default_location_dest_id.id
                        in_picking_type_id = self.receive_picking_type_id.id
                        in_res = order._prepare_picking(in_location_id, in_location_dest_id, in_picking_type_id)
                        in_picking = StockPicking.create(in_res)
                        order.order_line_ids._create_stock_moves(in_picking, type='in', warehouse = self.warehouse_id, location_id = in_location_id, location_dest_id = in_location_dest_id)
                        # in_picking.message_post_with_view('mail.message_origin_link',
                        #                            values={'self': in_picking,
                        #                                    'origin': order},
                        #                            subtype_id=self.env.ref('mail.mt_note').id)
                        in_picking.action_confirm()

                    else:
                        for rule in self.route_id.rule_ids:
                            if rule.picking_type_id.id == self.receive_picking_type_id.id:
                                location_src_id = rule.location_src_id.id
                        in_location_id = location_src_id
                        in_location_dest_id = self.receive_picking_type_id.default_location_dest_id.id
                        in_picking_type_id = self.receive_picking_type_id.id
                        in_res = order._prepare_picking(in_location_id, in_location_dest_id, in_picking_type_id)
                        in_picking = StockPicking.create(in_res)
                        order.order_line_ids._create_stock_moves(in_picking, type='in', warehouse = self.warehouse_id, location_id = in_location_id, location_dest_id = in_location_dest_id)
                        in_picking.action_confirm()
                else:
                    in_picking = in_pickings[0]
                    order.order_line_ids._create_stock_moves(in_picking, type='in', warehouse = False, location_id = False, location_dest_id=False)
                    # in_picking.message_post_with_view('mail.message_origin_link',
                    #                                values={'self': in_picking,
                    #                                        'origin': order},
                    #                                subtype_id=self.env.ref('mail.mt_note').id)
                    in_picking.action_confirm()
            if any([ptype in ['product', 'consu'] for ptype in order.order_line_ids.mapped('product_id.type')]):
                out_pickings = order.picking_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel') and x.picking_type_id.code == 'outgoing')
                if not out_pickings:
                    if self.supply_warehouse_id.delivery_steps == 'pick_ship':
                        output_location = self.supply_warehouse_id.wh_output_stock_loc_id
                        pick_type = self.supply_warehouse_id.pick_type_id
                        delivery_type = self.supply_warehouse_id.out_type_id
                        picking_res = order._prepare_picking(pick_type.default_location_src_id.id, pick_type.default_location_dest_id.id, pick_type.id)
                        picking = StockPicking.create(picking_res)
                        order.order_line_ids._create_stock_moves(picking, type='pick', warehouse = self.supply_warehouse_id, location_id = pick_type.default_location_src_id.id, location_dest_id = pick_type.default_location_dest_id.id)
                        # picking.message_post_with_view('mail.message_origin_link',
                        #                            values={'self': picking,
                        #                                    'origin': order},
                        #                            subtype_id=self.env.ref('mail.mt_note').id)
                        picking.action_confirm()
                        for rule in self.route_id.rule_ids:
                            if rule.picking_type_id.id == self.supply_picking_type_id.id:
                                location_id = rule.location_dest_id.id

                        out_res = order._prepare_picking(delivery_type.default_location_src_id.id, location_id, delivery_type.id)
                        out_picking = StockPicking.create(out_res)
                        order.order_line_ids._create_stock_moves(out_picking, type='out',warehouse = self.supply_warehouse_id, location_id = delivery_type.default_location_src_id.id, location_dest_id = location_id)
                        # out_picking.message_post_with_view('mail.message_origin_link',
                        #                            values={'self': out_picking,
                        #                                    'origin': order},
                        #                            subtype_id=self.env.ref('mail.mt_note').id)
                        out_picking.action_confirm()
                    else:
                        for rule in self.route_id.rule_ids:
                            if rule.picking_type_id.id == self.supply_picking_type_id.id:
                                location_id = rule.location_dest_id.id
                        delivery_type = self.supply_warehouse_id.out_type_id
                        out_location_id = self.supply_picking_type_id.default_location_src_id.id if self.supply_picking_type_id and self.supply_picking_type_id.default_location_src_id else self.supply_warehouse_id.lot_stock_id.id
                        out_location_dest_id = location_id
                        out_picking_type_id = self.supply_picking_type_id.id
                        out_res = order._prepare_picking(out_location_id, out_location_dest_id, out_picking_type_id)
                        out_picking = StockPicking.create(out_res)
                        order.order_line_ids._create_stock_moves(out_picking, type='out',warehouse = self.supply_warehouse_id, location_id = delivery_type.default_location_src_id.id, location_dest_id = location_id)
                        out_picking.action_confirm()
                        # out_picking.message_post_with_view('mail.message_origin_link',
                        #                            values={'self': out_picking,
                        #                                    'origin': order},
                        #                            subtype_id=self.env.ref('mail.mt_note').id)
                else:
                    in_picking = in_pickings[0]
                    order.order_line_ids._create_stock_moves(out_picking, type='out', warehouse= False, location_id = False, location_dest_id=False)
                    # out_picking.message_post_with_view('mail.message_origin_link',
                    #                                values={'self': out_picking,
                    #                                        'origin': order},
                    #                                subtype_id=self.env.ref('mail.mt_note').id)
                    out_picking.action_confirm()
        return True

    def view_picking(self):
        """Хүргэлтийн захиалгууд харуулах функц"""
        context = self._context or {}
        if context.get('type'):
            type = context.get('type')
            pick_ids = []
            action = self.sudo().env.ref('stock.action_picking_tree_all').read()[0]
            for picking in self.picking_ids:
                if picking.picking_type_id.code == type:
                    pick_ids.append(picking.id)
            if len(pick_ids) > 1:
                action['domain'] = [('id', 'in', pick_ids)]
            elif pick_ids:
                action['views'] = [
                    (self.env.ref('stock.view_picking_form').id, 'form')]
                action['res_id'] = pick_ids[0]
        return action

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can not delete this transit order. You can only be deleted during the drafts!'))
        return super(InheritedStockTransitOrder, self).unlink()

    def action_force_cancel(self):
        self.mapped('picking_ids').action_force_cancel()
        self.action_cancel()
        self.write({'state': 'cancel'})


