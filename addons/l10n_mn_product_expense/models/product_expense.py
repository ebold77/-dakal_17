from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class ProductExpenseTransactionValue(models.Model):
    _name = 'product.expense.transaction.value'
    _description = 'Transaction value'
    _order = 'name'

    active = fields.Boolean('Идэвхитэй эсэх', default=True)
    name = fields.Char('Загварын нэр', required=True,)
    code = fields.Char('Загварын код', required=True,)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    warehouse_id = fields.Many2one('stock.warehouse', 'Хамааралтай агуулах')
    account_id = fields.Many2one('account.account', 'Данс', copy=False, required=True)
    categ_ids = fields.Many2many('product.category', string='Барааны ангилал', copy=False)

class ProductExpense(models.Model):
    _name = 'product.expense'
    _description = 'Product Expense'
    _order = 'create_date desc, name desc'
    _inherit = ['mail.thread', 'base.workflow']

    def _default_employee(self):
        return self.env.user.employee_id or False

    ##
    # Columns
    name = fields.Char(u'Дугаар', readonly=True, copy=False)
    description = fields.Text(u'Description')
    date_planned = fields.Date(u'Товлосон огноо', required=True,)
    company_id = fields.Many2one('res.company', readonly=True, copy=True, string="Company", index=True, default=lambda self: self.env.company)
    warehouse_id = fields.Many2one('stock.warehouse', 'Нийлүүлэх агуулах', required=True, copy=True)
    user_id = fields.Many2one('res.users', 'Хэрэглэгч', default=lambda self: self.env.user.id, readonly=True)
    validator_id = fields.Many2one('res.users', 'Баталсан хэрэглэгч', readonly=True, copy=False,)
    partner_id = fields.Many2one('res.partner', 'Харилцагч',
                                 help=u"Хэрэв ямар нэг борлуулалтанд зориулж дагалдах барааг зарлагадаж байгаа бол энд өөр харилцагч сонгоно.",)
    ##
    # Санхүү
    account_id = fields.Many2one('account.account', 'Данс', domain=[('internal_group', '=', 'expense')], required=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс/нэгж', copy=True,
                                    help=u"Хэрэв хэлтэс дээрх зардал бол сонгоно", readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Ажилтан', required=True, default=_default_employee)
    date_user = fields.Datetime('User Date', readonly=True, copy=False,)
    date_validator = fields.Datetime('Баталсан огноо', readonly=True, copy=False,)
    product_expense_line = fields.One2many('product.expense.line', 'expense_id', string='Expense line', copy=True,
                                           help=u"Бараа зарлагдах мэдээлэл")
    transaction_value_id = fields.Many2one('product.expense.transaction.value', 'Гүйлгээний загвар', ondelete='restrict', required=True)
    categ_ids = fields.Many2many(related="transaction_value_id.categ_ids", string='Барааны ангилал', readonly=True,)
    expense_picking_ids = fields.One2many('stock.picking', 'product_expense_id', 'Зарлага хийсэн хөдөлгөөнүүд', readonly=True, copy=False,)

    cost_total = fields.Float('Нийт үнэ', compute='_compute_cost_total', store=True)
    expense_picking_count = fields.Integer(u'Зарлагын баримтын тоо', readonly=True, compute='_compute_expense_picking_count', compute_sudo=True)

    @api.depends('product_expense_line')
    def _compute_cost_total(self):
        for expense in self:
            total = 0
            for line in expense.product_expense_line:
                total += line.cost
            expense.cost_total = total

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.sudo().department_id
            self.partner_id = self.employee_id.sudo().address_home_id
        else:
            self.department_id = False
            self.partner_id = False

    @api.onchange('transaction_value_id')
    def onchange_transaction_value(self):
        if self.transaction_value_id:
            self.account_id = self.transaction_value_id.account_id
            self.warehouse_id = self.transaction_value_id.warehouse_id

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        for line in self.product_expense_line:
            line.onchange_product_id()

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.name or "Ноорог"))
        return result

    # -------------- BEGIN: APPROVAL WORKFLOW RELATED LOGICS ------------------
    @api.model
    def _get_module_name(self):
        return 'l10n_mn_product_expense'

    @api.model
    def _get_action_name(self):
        return 'action_product_expense'

    def _when_state_done(self):
        self.action_to_confirm()

    def _when_state_sent(self):
        self.action_to_send()

    def _when_state_cancel(self):
        self.action_to_cancel()
    # --------------- END: APPROVAL WORKFLOW RELATED LOGICS ------------------

    def get_prepare_stock_move_line(self, line, sp_id, desc, dest_loc):
        return {
            'name': desc,
            'picking_id': sp_id.id,
            'product_id': line.product_id.id,
            'product_uom': line.product_id.uom_id.id,
            'product_uom_qty': line.qty,
            'location_id': self.warehouse_id.lot_stock_id.id,
            'location_dest_id': dest_loc.id,
            'state': 'draft'
        }

    def unlink(self):
        for expense in self:
            if expense.state_type not in ('draft'):
                raise UserError(_('You cannot delete a product expense which is done. You should reopen it instead.'))
        return super(ProductExpense, self).unlink()

    def action_to_confirm(self):
        dest_loc = self.env['stock.location'].sudo().search(
            [('usage', '=', 'customer')], limit=1)

        if not dest_loc:
            raise UserError(_(u'Зарлагадах байрлал олдсонгүй!'))

        tran_value = ""
        if self.transaction_value_id:
            tran_value = self.transaction_value_id.name + ', '
        if self.description:
            tran_value += self.description

        sp_id = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse_id.out_type_id.id,
            'state': 'draft',
            'move_type': 'one',
            'partner_id': self.partner_id.id or False,
            'scheduled_date': self.date_planned,
            'location_id': self.warehouse_id.lot_stock_id.id,
            'location_dest_id': dest_loc.id,
            'origin': self.name + u' - Бусад зарлага хийх, ' + tran_value,
            'product_expense_id': self.id,
        })

        for line in self.product_expense_line:
            desc = self.name + ' - ' + tran_value
            vals = self.get_prepare_stock_move_line(line, sp_id, desc, dest_loc)
            self.env['stock.move'].create(vals)

        con = dict(self._context)
        con['from_code'] = True

        sp_id.with_context(con).action_confirm()
        sp_id.scheduled_date = self.date_planned

        # Батлах
        self.validator_id = self.env.user.id
        self.date_validator = datetime.now()
        self.message_post(body=u"%s - батлагдлаа" % self.validator_id.name)

    def action_to_send(self):
        if self.product_expense_line:
            if not self.name:
                self.name = self.env['ir.sequence'].next_by_code('product.expense')
            self.user_id = self.env.user.id
            self.date_user = datetime.now()
        else:
            raise UserError(_(u'Бараа зарлагадах мэдээллийг оруулна уу!'))
        tran_value = ""
        if self.transaction_value_id:
            tran_value = self.transaction_value_id.name + ', '
        if self.description:
            tran_value += self.description

    def action_to_cancel(self):
        self.expense_picking_ids.action_cancel()

    @api.depends('expense_picking_ids')
    def _compute_expense_picking_count(self):
        for item in self:
            item.expense_picking_count = len(item.expense_picking_ids)

    def action_view_expense_picking_ids(self):
        tree_view_id = self.env.ref('stock.vpicktree').id
        form_view_id = self.env.ref('stock.view_picking_form').id
        return {
            'name': 'Хөдөлгөөн',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('id', 'in', self.expense_picking_ids.ids)],
            'context': {},
        }

class ProductExpenseLine(models.Model):
    _name = 'product.expense.line'
    _description = 'Product Expense Line'

    categ_ids = fields.Many2many(related="expense_id.transaction_value_id.categ_ids", string='Барааны ангилал', readonly=True)
    expense_id = fields.Many2one('product.expense', u'БМ шаардах', ondelete='cascade')
    product_id = fields.Many2one('product.product', u'Бараа', required=True)
    uom_id = fields.Many2one(related='product_id.uom_id', string=u'Хэмжих нэгж', store=True, readonly=True,)
    categ_id = fields.Many2one(related='product_id.categ_id', string=u'Ангилал', store=True, readonly=True,)
    qty = fields.Float(u'Тоо хэмжээ', required=True, default=1,)
    available_qty = fields.Float('Үлдэгдэл', copy=False, default=0)
    cost = fields.Float(u'Дэд дүн', compute='_compute_cost', store=True)
    state_type = fields.Char(related='expense_id.state_type')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    company_id = fields.Many2one(comodel_name="res.company", related="expense_id.company_id", string="Company", store=True,)
    employee_id = fields.Many2one(string=u'Ажилтан', related='expense_id.employee_id', store=True)
    date_planned = fields.Date(string=u'Товолсон огноо', related='expense_id.date_planned', store=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.product_id.name))
        return result

    @api.depends('product_id', 'qty')
    def _compute_cost(self):
        for line in self:
            line.cost = line.product_id.standard_price * line.qty

    @api.onchange('product_id')
    def onchange_product_id(self):
        quants = self.env['stock.quant']
        if self.expense_id.warehouse_id:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id.warehouse_id', '=', self.expense_id.warehouse_id.id),
                ('location_id.usage', '=', 'internal')
            ])
        else:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id.usage', '=', 'internal')
            ])
        self.available_qty = self.product_id.with_context({'warehouse': self.warehouse_id.id, 'to_date': self.date_planned}).qty_available
