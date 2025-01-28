# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp

class LicemedRegistration(models.Model):

    _name = "product.licemed.registration"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Product Licemed Registration"
    _order = 'name desc, id desc'

    name = fields.Char('Reference', index=True, copy=False, default='New')
    tbltNameSales = fields.Char('Mon Name', )
    tbltNameInter = fields.Char('Inter Name', )
    tbltBarCode = fields.Char('BarCode')
    tbltSizeMixture = fields.Char('tblt Size Mixture', )
    tbltSizeUnit = fields.Char('tblt Size Unit', )
    tbltType = fields.Char('tblt Type', )
    conditions_granting = fields.Selection([
        ('prescription', 'Жороор'),
        ('no_prescription', 'Жоргүй'),
        ('prescription_psychotropic', 'Cэтгэцэд нөлөөт эмийн жороор'),
        ('prescription_drug', 'Мансууруулах эмийн жороор'),
        ('use_medical', 'Эмнэлгийн нөхцөлд хэрэглэнэ')
    ], string='Conditions Granting')
    tbltManufacture = fields.Char('Manufacture',)
    registered_company = fields.Char('Registered Company')
    validity_period = fields.Date(string='Validity period')
    state = fields.Selection([
        ('registered', 'Registered'),
        ('expired', 'Registration period has expired'),
        ('removed', 'Removed from the register'),
        ('suspended', 'Suspended'),
    ], string='Status', index=True, copy=False, default='registered')
