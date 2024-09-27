
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import exceptions
import odoo.addons.decimal_precision as dp  # @UnresolvedImport
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    package_qty = fields.Integer('Quantity in the package')
    insurance_list_id = fields.Many2one('insurance.discount.list', string="Insurance List")
    
    @api.onchange('insurance_list_id')
    def onchange_insurance_list_id(self):
        rec = self.insurance_list_id.id
        res = self.env['insurance.discount.list'].browse(rec)
        res.write({'product_ids':[(4,self._origin.id)]})