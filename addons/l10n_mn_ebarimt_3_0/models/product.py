# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class product_template(models.Model):
    _inherit = 'product.template'
    
    ebarimt_gs1barcode_id = fields.Many2one('ebarimt.gs1barcode',string='EBarimt GS1 barcode',compute='_compute_ebarimt_gs1barcode_id',inverse='_set_ebarimt_gs1barcode_id')
    tax_type = fields.Char(compute='_tax_type', string='EBarimt VAT type')

    @api.depends('product_variant_ids', 'product_variant_ids.ebarimt_gs1barcode_id')
    def _compute_ebarimt_gs1barcode_id(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.ebarimt_gs1barcode_id = template.product_variant_ids.ebarimt_gs1barcode_id
        for template in (self - unique_variants):
            template.ebarimt_gs1barcode_id = None

    def _set_ebarimt_gs1barcode_id(self):
        self.ensure_one()

        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.ebarimt_gs1barcode_id = self.ebarimt_gs1barcode_id

    # @api.onchange('ebarimt_gs1barcode_id')
    # def onchange_ebarimt_gs1barcode_id(self):
    #     self.barcode = self.ebarimt_gs1barcode_id.code

    @api.depends('taxes_id')
    def _tax_type(self):
        for product in self:
            product.tax_type = ', '.join(str(ebarimt_tax.name) for ebarimt_tax in set(product.taxes_id.mapped('ebarimt_tax_type_id')))

class product_product(models.Model):
    _inherit = 'product.product'
    tax_type = fields.Char(compute='_tax_type', string='EBarimt VAT type')
    ebarimt_gs1barcode_id = fields.Many2one('ebarimt.gs1barcode', string='EBarimt GS1 barcode')

    # @api.onchange('ebarimt_gs1barcode_id')
    # def onchange_ebarimt_gs1barcode_id(self):
    #     self.barcode = self.ebarimt_gs1barcode_id.code

    @api.depends('taxes_id')
    def _tax_type(self):
        for product in self:
            product.tax_type = ', '.join(str(ebarimt_tax.name) for ebarimt_tax in set(product.taxes_id.mapped('ebarimt_tax_type_id')))
