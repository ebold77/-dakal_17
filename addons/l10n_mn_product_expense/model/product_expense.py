# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError

class ProductExpense(models.Model):
    _name = 'product.expense'
    _description = 'Product Expense'
    _inherit = ['mail.thread']

    STATE_SELECTION = [('draft', 'Draft'),
                       ('waiting_approve', 'Waiting for approve'),
                       ('approved', 'Approved'),
                       ('returned', 'Returned'),
                       ('done', 'Done'),
                       ('refused', 'Refused'),
                       ('cancel', 'Cancelled'), ]

    def _default_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if len(employee) > 1:
            employee = employee[0]
        if not employee:
            raise exceptions.AccessError(_("Can't find any related employee for your user. Only employee can create bill of expense."))
        return employee.id

    def _compute_is_stock_manager(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            self.is_stock_manager = True
        else:
            self.is_stock_manager = False

    def _default_warehouse_id(self):
        default_warehouse = self.env.user.allowed_warehouse_ids.ids
        warehouse_ids = self.env['stock.warehouse'].search([('id', 'in', default_warehouse), ('company_id', 'in', self.env.company.ids)], limit=1)
        return warehouse_ids

    def _domain_warehouses(self):
        return [
            ('id', 'in', self.env.user.allowed_warehouse_ids.ids),
            '|', ('company_id', '=', False), ('company_id', 'in', self.env.company.ids)
        ]

    def _count_out_stock_picking(self):
        stock_picking = self.env['stock.picking'].search([('expense_id', '=', self.id)])
        self.count_out_stock_picking = len(stock_picking)

    def _compute_must_choose_account(self):
        if self.workflow_id:
            if self.check_sequence == len(self.workflow_id.line_ids):
                self.must_choose_account = True
            else:
                self.must_choose_account = False
        else:
            self.must_choose_account = False

    @api.depends('expense_line_ids')
    def _compute_total_amount(self):
        for obj in self:
            total_amount = 0
            for line in obj.expense_line_ids:
                total_amount += line.price_subtotal
            obj.total_amount = total_amount

    name = fields.Char('Name', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_default_warehouse_id, domain=_domain_warehouses, required=True, tracking=True)
    stock_picking_type_id = fields.Many2one('stock.picking.type', string="Location", domain="[('code', '=', 'outgoing'),('warehouse_id','=',warehouse_id)]", required=True, tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', default=_default_employee, required=True, tracking=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, required=True, tracking=True)
    cost_center = fields.Selection(related='company_id.cost_center', readonly=True, string='Cost center')
    date = fields.Date(string='Date', default=datetime.today(), tracking=True)
    account_id = fields.Many2one('account.account', 'Account', tracking=True)
    req_analytic_account = fields.Boolean(related='account_id.req_analytic_account', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic account', tracking=True)
    state = fields.Selection(STATE_SELECTION, default='draft', tracking=True)
    expense_line_ids = fields.One2many('product.expense.line', 'expense_id', 'Expense line',
                                   states={'approved': [('readonly', True)],
                                           'done': [('readonly', True)]}, copy=True)
    product_id = fields.Many2one('product.product', 'Product', related='expense_line_ids.product_id')
    workflow_id = fields.Many2one('workflow.config', 'Workflow', copy=False)
    check_sequence = fields.Integer('Workflow Step', default=0, copy=False)
    history_line_ids = fields.One2many('product.expense.workflow.history', 'history_id', 'Workflow History', copy=False)
    is_validator = fields.Boolean(compute='_compute_is_validator')
    is_creator = fields.Boolean(compute='_compute_is_creator')
    count_out_stock_picking = fields.Integer(compute='_count_out_stock_picking')
    stock_picking_ids = fields.One2many('stock.picking', 'expense_id', 'Stock picking')
    must_choose_account = fields.Boolean(compute='_compute_must_choose_account')
    is_stock_manager = fields.Boolean(compute='_compute_is_stock_manager')
    total_amount = fields.Float('Total Amount', compute='_compute_total_amount')
    description = fields.Text('Description')

    @api.onchange('department_id')
    def onchange_department(self):
        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id', 'child_of', self.department_id.id)])
            if self.employee_id not in employees:
                self.employee_id = False
        else:
            employees = self.env['hr.employee'].search([])
        return {
            'domain': {
                'employee_id': [('id', 'in', employees.ids)]
            }
        }

    @api.onchange('cost_center', 'warehouse_id')
    def set_analytic_account(self):
        for obj in self:
            if obj.cost_center == 'warehouse':
                obj.analytic_account_id = obj.warehouse_id.analytic_account_id
                for line in obj.expense_line_ids:
                    line.analytic_account_id = obj.warehouse_id.analytic_account_id
            else:
                obj.analytic_account_id = False
                for line in obj.expense_line_ids:
                    line.analytic_account_id = False

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id

    @api.onchange('account_id')
    def _onchange_account(self):
        lines_to_change = self.env['product.expense.line']
        for line in self.expense_line_ids:
            if not line.account_id or self._origin.account_id.id == line.account_id.id:
                lines_to_change |= line
        lines_to_change.write({'account_id': self.account_id.id})

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        # Шаардахын дансыг соливол мөрүүдийн дансыг сонгогдсон эсэхээс үл хамааран шаардахын дансаар сольдог болгов
        for obj in self:
            for line in obj.expense_line_ids:
                line.analytic_account_id = obj.analytic_account_id

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        # filter stock picking
        if self.warehouse_id:
            for obj in self:
                stock_picking_type = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', obj.warehouse_id.id), ('code', '=', 'outgoing')], limit=1)
                if stock_picking_type:
                    obj.stock_picking_type_id = stock_picking_type.id
                if obj.warehouse_id._fields.get('stock_account_output_id'):
                    obj.account_id = obj.warehouse_id.stock_account_output_id
        for line in self.expense_line_ids:
            line.warehouse_id = obj.warehouse_id.id
        self.account_id = self.warehouse_id.expense_account_id
        # create warehouse domain
        domain = {}
        _warehouses = []
        for warehouse in self.env.user.allowed_warehouse_ids:
            _warehouses.append(warehouse.id)
        if _warehouses:
            domain['warehouse_id'] = [('id', 'in', _warehouses)]
        return {'domain': domain}

    def action_view_expense(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        pick_ids = self.env['stock.picking'].search([('expense_id', '=', self.id)]).ids
        if len(pick_ids) > 1 or len(pick_ids) == 0:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result

    @api.depends('check_sequence')
    def _compute_is_validator(self):
        for rec in self:
            history_obj = self.env['product.expense.workflow.history']
            validators = history_obj.search([('history_id', '=', rec.id), ('line_sequence', '=', rec.check_sequence)], limit=1, order='sent_date DESC').user_ids
            if self.env.user in validators:
                rec.is_validator = True
            else:
                rec.is_validator = False

    def _compute_is_creator(self):
        for rec in self:
            if rec.create_uid == self.env.user:
                rec.is_creator = True
            else:
                rec.is_creator = False

    def unlink(self):
        model_obj = self.env['ir.model.data']
        stock_manager_group = model_obj.get_object('stock', 'group_stock_manager')
        stock_manager = self.env['res.users'].search([('groups_id', 'in', stock_manager_group.id)])
        for line in self:
            if line.state == 'draft' or line.state == 'refused':
                if self.env.user not in stock_manager:
                    if self.env.user == line.create_uid:
                        super(ProductExpense, line).unlink()
                    else:
                        raise UserError(_('Product expense delete only own!'))
                else:
                    super(ProductExpense, line).unlink()
            else:
                raise UserError(_('Product expense delete only draft state!'))

    def cancel(self):
        for expense in self:
            for pick in expense.stock_picking_ids:
                if pick.state in ('done'):
                    raise UserError(
                        _('Cannot cancel product expense !\n Because picking state is Done of reception attached to this product expense.'))
                else:
                    pick.action_cancel()
                    pick.unlink()
        self.state = 'cancel'

    def draft(self):
        self.ensure_one()
        self.check_sequence = 0
        self.state = 'draft'
        self.workflow_id = False

    def send(self):
        """    Ажлын урсгалыг 1. Шаардахын агуулахаас хайна
                              2. Агуулахад тохируулаагүй тохиолдолд Агуулахын тохиргооны Шаардахын ажлын урсгалаас хайна
                              3. Агуулахын тохиргоонд тохируулаагүй тохиолдолд Ажлын урсгалын бүртгэлээс ажилтны хэлтсээр хайна.
        """
        for expense in self:
            workflow = ''
            if expense.warehouse_id and expense.warehouse_id.workflow_id:
                workflow = expense.warehouse_id.workflow_id.id
            elif expense.env.user.company_id.workflow_id:
                workflow = self.env.user.company_id.workflow_id.id
            else:
                workflow = self.env['workflow.config'].get_workflow('employee', 'product.expense', expense.employee_id.id, None)
            if not workflow:
                raise exceptions.Warning(_('There is no workflow defined!'))

            expense.workflow_id = workflow
            if workflow:
                # Шаардахын мөр байгаа эсэхийн шалгаж байна
                if expense.expense_line_ids:
                    success, current_sequence = self.env['workflow.config'].send('product.expense.workflow.history',
                                                                                 'history_id', expense, expense.create_uid.id)
                    if success:
                        expense.check_sequence = current_sequence
                        expense.state = 'waiting_approve'
                        expense.name = self.env['ir.sequence'].get('product.expense')
                else:
                    raise UserError(_('Product expense line is not created'))

    def check_quanitity(self, lines):
        product_name = []
        for line in lines:
            if line.available_qty < line.quantity:
                product_name.append('[' + line.product_id.default_code if line.product_id.default_code else ' ' + '] ' + str(line.product_id.name))
        return product_name

    @api.model
    def _check_analytic_account(self):
        for line in self.expense_line_ids:
            if line.account_id and line.account_id.req_analytic_account:
                if line.analytic_account_id:
                    continue
                else:
                    raise UserError(_('The selected account requires a analytic account, so please select the analytic account on the line'))

    def approve(self):
        # Данс сонгосон тохиолдолд тухайн данс нь Шинжилгээний данс шаардах данс бол Шинжилгээний данс сонгохыг шаардана
        self._check_analytic_account()
        if self.workflow_id:
            success, sub_success, current_sequence = self.env['workflow.config'].approve('product.expense.workflow.history', 'history_id', self, self.env.user.id)
            if success:
                if sub_success:
                    check_list = self.check_quanitity(self.expense_line_ids)
                    if self.company_id.type_approve_expense == '0':
                        if len(check_list) > 0:
                            raise UserError(_(u'Not enough quantity!. Product %s') % ', '.join(check_list))
                        else:
                            for line in self.expense_line_ids:
                                if not line.quantity:
                                    raise UserError(_('The number of product expense quantity is 0'))
                    self.create_out_picking()
                    self.state = 'approved'
                else:
                    self.check_sequence = current_sequence

    def refuse(self):
        if self.workflow_id:
            success = self.env['workflow.config'].reject('product.expense.workflow.history', 'history_id', self, self.env.user.id)
            if success:
                pickings = self.env['stock.picking'].search([('expense_id', '=', self.id)])
                if pickings:
                    for picking in pickings:
                        picking.unlink()
                self.state = 'refused'
#
    def previous(self):
        if self.workflow_id:
            success, current_sequence = self.env['workflow.config'].action_return('product.expense.workflow.history',
                                                                                  'history_id', self, self.env.user.id)
            if success:
                self.check_sequence = current_sequence

    def action_force_cancel(self):
        self.mapped('stock_picking_id').action_force_cancel()
        self.cancel()

    def create_out_picking(self):
        """Шаардахаас хүргэлтийн захиалга үүсгэх функц"""
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        des_location = self.env['stock.location'].search([('scrap_location', '=', True)])
        for record in self:
            # Данс нь авлага болон өглөг төрөлтэй үед хүргэх захиалгаас ажил гүйлгээ үүсэхдээ харилцагч авч үүсдэг
            # болгох. Шаардах хуудас үүсгэсэн ажилтантай холбоотой харилцагчийг авна.
            if str(record.account_id.user_type_id.type) in ('receivable', 'payable'):
                values = {'expense_id': record.id,
                          'origin': record.name,
                          'company_id': record.company_id.id,
                          'picking_type_id': self.stock_picking_type_id.id,
                          'location_dest_id': des_location[0].id,
                          'location_id': self.stock_picking_type_id.default_location_src_id.id,
                          'partner_id': record.employee_id.address_home_id.id or False}
            else:
                values = {'expense_id': record.id,
                          'origin': record.name,
                          'company_id': record.company_id.id,
                          'picking_type_id': self.stock_picking_type_id.id,
                          'location_dest_id': des_location[0].id,
                          'location_id': self.stock_picking_type_id.default_location_src_id.id}
            stock_picking_object = StockPicking.create(values)
            stock_picking_object.message_post_with_view(
                'l10n_mn_product_expense.message_link_for_picking_expense',
                values={
                    'self': stock_picking_object,
                    'origin': record
                },
                subtype_id=self.env.ref('mail.mt_note').id
            )
            if record.expense_line_ids:
                for line in record.expense_line_ids:
                    move_lines_values = line._get_stock_move_vals(stock_picking_object.id, self.stock_picking_type_id.default_location_src_id.id, des_location[0].id)
                    StockMove.sudo().create(move_lines_values)

    def check_done(self):
        ''' шаардах хуудаснаас үүссэн барааны гарах хөдөлгөөн батлагдаж дуусахад
        "Дууссан" төлөвт орох
        '''
        ok = True
        for picking in self.stock_picking_ids:
            if picking.picking_type_id.code == 'outgoing' and picking.state not in ('done'):
                ok = False
        if ok:
            self.state = 'done'

class ExpenseLine(models.Model):
    _name = 'product.expense.line'
    _description = 'Product Expense Line'

    def _get_stock_move_vals(self, picking_id, location_id, location_dest_id):
        vals = {}
        vals.update({'name': self.name})
        vals.update({'origin': self.expense_id.name})
        vals.update({'picking_type_id': self.expense_id.stock_picking_type_id.id})
        vals.update({'picking_id': picking_id})
        vals.update({'product_id': self.product_id.id})
        vals.update({'product_uom': self.product_id.product_tmpl_id.uom_id.id})
        vals.update({'location_id': location_id})
        vals.update({'location_dest_id': location_dest_id})
        vals.update({'product_uom_qty': self.quantity})
        vals.update({'company_id': self.expense_id.company_id.id})
        return vals

    @api.depends('product_id','warehouse_id')
    def _compute_available_qty(self):
        if not self.warehouse_id:
            raise UserError(_('Warning!\nYou must select supply warehouse before add expense line!'))
        for obj in self:
            if obj.product_id:
                obj.available_qty = obj.product_id.get_qty_availability([obj.expense_id.stock_picking_type_id.default_location_src_id.id], obj.expense_id.date, qty_dp_digit=self.env['decimal.precision'].precision_get('Expense Available Qty'))
                obj.name = obj.product_id.name_get()[0][1]
            else:
                obj.available_qty = 0

    @api.depends('quantity', 'product_id')
    def _compute_price(self):
        for line in self:
            line.price_subtotal = line.standard_price * line.quantity

    @api.depends('product_id')
    def _compute_standard_price(self):
        for line in self:
            line.standard_price = line.product_id.standard_price

    expense_id = fields.Many2one('product.expense', 'Expense', ondelete='cascade')
    name = fields.Char('Name', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True, domain=[('type', '!=', 'service')])
    quantity = fields.Float('Quantity', digits='Expense Quantity')
    returned_quantity = fields.Float('Returned Quantity', readonly=True, digits='Expense Returned Quantity')
    available_qty = fields.Float(compute='_compute_available_qty', string='Available quantity', digits='Expense Available Qty')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic account')
    product_type = fields.Selection(related='expense_id.stock_picking_ids.move_lines.state', related_sudo=False, string='Product type')
    must_choose_account = fields.Boolean(related='expense_id.must_choose_account')
    standard_price = fields.Float(readonly=True, compute='_compute_standard_price', digits='Expense product cost')
    price_subtotal = fields.Float(string='Amount', store=True, readonly=True, compute='_compute_price')
    date = fields.Date(related='expense_id.date', string='Date', store=True)
    company_id = fields.Many2one('res.company',related='expense_id.company_id', string='Company', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    state = fields.Selection(related='expense_id.state', string='State', store=True)

    @api.constrains('quantity')
    def _check_quantity_value(self):
        for line in self:
            if line.quantity <= 0:
                raise UserError(_('Error!\nProduct quantitiy must be greater than Zero.'))

class ExpenseWorkflowHistory(models.Model):
    _name = 'product.expense.workflow.history'
    _description = 'Product Expense Workflow History'
    _order = 'history_id, sent_date'

    STATE_SELECTION = [('waiting', 'Waiting'),
                       ('confirmed', 'Confirmed'),
                       ('approved', 'Approved'),
                       ('return', 'Return'),
                       ('rejected', 'Rejected')]

    history_id = fields.Many2one('product.expense', 'Expense', readonly=True, ondelete='cascade')
    line_sequence = fields.Integer('Workflow Step')
    name = fields.Char('Verification Step', readonly=True)
    user_ids = fields.Many2many('res.users', 'res_users_expense_workflow_history_ref', 'history_id', 'user_id', 'Validators')
    sent_date = fields.Datetime('Sent date', required=True, readonly=True)
    user_id = fields.Many2one('res.users', 'Validator', readonly=True)
    action_date = fields.Datetime('Action date', readonly=True)
    action = fields.Selection(STATE_SELECTION, 'Action', readonly=True)