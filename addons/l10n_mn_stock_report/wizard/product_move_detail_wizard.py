# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class ProductMoveDetailReport(models.TransientModel):
    _name = "product.move.detail.report"
    _description = "product move detail report"

    # def domain_warehouses(self):
    #     return [('id', 'in', self.warehouse_ids.ids)]

    def get_locations(self):
        loc_ids = []
        for warehouse in self.warehouse_ids.filtered(lambda x: x.company_id == self.env.company):
            locations = self.env['stock.location'].search([('id', 'child_of', [warehouse.lot_stock_id.id])])
            loc_ids.extend(locations.ids)
        return [('id', 'in', loc_ids)]

    date_start = fields.Date(required=True, string='Эхлэх огноо', default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date(required=True, string='Дуусах огноо', default=lambda *a: time.strftime('%Y-%m-%d'))
    product_tmpl_ids = fields.Many2many('product.template', string='Бараа', help="Тайланд гарах бараануудыг сонгоно")
    warehouse_ids = fields.Many2many('stock.warehouse', string='Агуулах', )
    location_ids = fields.Many2many('stock.location', string='Байрлал', )
    product_ids = fields.Many2many('product.product', string='Барааны хувилбар', help="Тайланд гарах барааг сонгоно")
    categ_ids = fields.Many2many('product.category', string='Барааны ангилал', help="Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
    assigned_user_id = fields.Many2one('res.users', string='Нөөцөлсөн хэрэглэгч')
    included_internal = fields.Boolean(string='Дотоод хөдөлгөөн оруулахгүй', default=False)
    move_type = fields.Selection([
        ('income_expense', 'Эхний үлдэгдэл/Орлого/Зарлага/Эцсийн үлдэгдэл'),
        ], default='income_expense', required=True, string='Төрөл')
    move_state = fields.Selection([
        ('cancel', 'Бүгд'),
        ('assigned_done', 'Бэлэн болон Дууссан'),
        ('confirmed', 'Бэлэн болохыг хүлээж байгаа'),
        ('assigned', 'Бэлэн'),
        ('done', 'Дууссан'),
    ], default='done', string='Төлөв', required=True,)

    import_wh = fields.Boolean('Бүх агуулах ОРУУЛАХ/АРИЛГАХ', default=False)

    @api.onchange('import_wh')
    def onchange_all_wh_import(self):
        if self.import_wh:
            self.warehouse_ids = self.env['stock.warehouse'].search(([]))
        else:
            self.warehouse_ids = False

    @api.onchange('warehouse_ids')
    def onchange_location(self):
        if self.warehouse_ids:
            loc_ids = []
            for warehouse in self.warehouse_ids.filtered(lambda x: x.company_id == self.env.company):
                locations = self.env['stock.location'].search([('id', 'child_of', [warehouse.lot_stock_id.id])])
                loc_ids.extend(locations.ids)
                self.location_ids = loc_ids
        else:
            self.location_ids = False

    def get_domain(self, domain):
        if self.move_type == 'income_expense':
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id', 'in', self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id', 'in', self.categ_ids.ids))
            if self.move_state == 'cancel':
                domain.append(('state', '!=', self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state', 'in', ['done', 'assigned']))
            else:
                domain.append(('state', '=', self.move_state))
            if self.location_ids:
                domain.append(('location_id', 'in', self.location_ids.ids))
            elif self.warehouse_ids:
                domain.append(('warehouse_id', 'in', self.warehouse_ids.ids))
            if self.included_internal:
                domain.append(('transfer_type', '!=', 'internal'))
            domain.append('|')
            domain.append(('date_balance', '<', self.date_start))
            domain.append('&')
            domain.append(('date_expected', '<=', self.date_end))
            domain.append(('date_expected', '>=', self.date_start))
        return domain

    def open_analyze_view(self):
        domain = []
        if self.move_type == 'income_expense':
            action = self.env.ref('l10n_mn_stock_report.action_stock_report_detail').sudo()
        vals = action.read()[0]
        vals['domain'] = self.get_domain(domain)
        return vals
