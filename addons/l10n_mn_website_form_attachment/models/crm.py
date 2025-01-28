# -*- coding: utf-8 -*-

from odoo import fields, models


class Lead(models.Model):
    _inherit = 'crm.lead'
    attachment = fields.Binary(string=u'Компаний гэрчилгээ', attachment=True)
    attachment_b = fields.Binary(string=u'Компаний гэрчилгээ ар тал', attachment=True)
    attachment1 = fields.Binary(string=u'Тусгай зөвшөөрөл', attachment=True)
    attachment1_b = fields.Binary(string=u'Тусгай зөвшөөрөл ар тал', attachment=True)
    attachment2 = fields.Binary(string=u'Захирлын иргэний үнэмлэх', attachment=True)
    attachment2_b = fields.Binary(string=u'Захирлын иргэний үнэмлэх ар тал', attachment=True)
   


    def website_form_input_filter(self, request, values):
        values = super(Lead, self).website_form_input_filter(request, values)
        print('valus==========', values)
        return values