# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import exceptions
import odoo.addons.decimal_precision as dp  # @UnresolvedImport
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    package_qty = fields.Integer('Quantity in the package')
    emd_insurance_list_id = fields.Many2one('emd.insurance.discount.list', string="Insurance List")
    
    @api.onchange('emd_insurance_list_id')
    def onchange_insurance_list_id(self):
        rec = self.emd_insurance_list_id.id
        res = self.env['emd.insurance.discount.list'].browse(rec)
        res.write({'product_ids':[(4,self._origin.id)]})


# class ProductProduct(models.Model):
#     _inherit = 'product.product'

#     package_qty = fields.Integer(related='product_tmpl_id.package_qty', string='Quantity in the package')