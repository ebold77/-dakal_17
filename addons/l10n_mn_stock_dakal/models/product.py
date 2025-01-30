# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo import exceptions
import odoo.addons.decimal_precision as dp  # @UnresolvedImport
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

   
    register_id = fields.Many2one('product.licemed.registration', string="Licemed Registration")
    package_qty = fields.Char('Quantity in the package')
    general_category_id = fields.Many2one('product.general.category', 'General Category')
    tbltSizeMixture = fields.Char('Size Mixture', )
    tbltType = fields.Char('tblt Type', )
    tbltManufacture = fields.Char('Manufacture',)
    conditions_granting = fields.Selection([
        ('prescription', 'Жороор'),
        ('no_prescription', 'Жоргүй'),
        ('prescription_psychotropic', 'Cэтгэцэд нөлөөт эмийн жороор'),
        ('prescription_drug', 'Мансууруулах эмийн жороор'),
        ('use_medical', 'Эмнэлгийн нөхцөлд хэрэглэнэ')
    ], string='Conditions Granting')
    
    @api.onchange('register_id')
    def onchange_register_id(self):
        package_qty = 0
        
        if self.register_id:
            if self.register_id.tbltSizeUnit.isnumeric():
                package_qty = self.register_id.tbltSizeUnit
            else:
                aaa = re.split(r'(\d+)', self.register_id.tbltSizeUnit)
                
                b = c = d = count = 0
                for a in aaa:
                    if a.isnumeric() and count==0:
                        b = a
                        count =1

                    elif a.isnumeric() and count==1:
                        c = a
                        count =2
                    elif a.isnumeric() and count==2:
                        d = a
                        count =3
                if count == 1:
                    package_qty = int(b)
                elif count == 2:
                    package_qty = int(b) * int(c)
                elif count == 3:
                    package_qty = int(b) * int(c) * int(d)
   
            if self.register_id.state != 'registered':
                raise UserError(_("You can only create items from a drug registry that has a registered status."))
            else:
                self.write({
                    'name':self.register_id.tbltNameSales +' '+self.register_id.tbltSizeMixture+' №'+self.register_id.tbltSizeUnit,
                    'barcode':self.register_id.tbltBarCode,
                    'package_qty': package_qty,
                    'tbltSizeMixture': self.register_id.tbltSizeMixture,
                    'tbltType': self.register_id.tbltType,
                    'conditions_granting': self.register_id.conditions_granting,
                    'tbltManufacture': self.register_id.tbltManufacture,
                    })