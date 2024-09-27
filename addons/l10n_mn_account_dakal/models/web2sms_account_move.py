# -*- coding: utf-8 -*-
##############################################################################
#
#    Dakal Pharma LLC, Enterprise Management Solution
#    Copyright (C) 2001-2019 Dakal Pharma LLC (<http://www.dklgr.mn/;). All Rights Reserved
#
#    Email : info@dakal.mn
#    Phone : 976 + 95762987, 976 + 99065724
#
##############################################################################

import logging
from urllib.request import urlopen
import re
from datetime import datetime
import simplejson as json

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

    
class account_move(models.Model):
    _inherit = 'account.move'
    
    def _sms_count(self):
        res = {}
        for obj in self:
            obj_ids = self.env['web.to.sms'].search([('invoice_id', '=', obj.id)])
            self.sms_ids = obj_ids
            self.sms_count = len(obj_ids)

   
    sms_ids = fields.One2many('web.to.sms', 'invoice_id', readonly=True)
    sms_count = fields.Integer(compute='_sms_count', string='Sms', type='integer')

    def action_web2sms(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dakal_account.action_web_to_sms_tree')
        action['context'] = {}
        action['domain'] = [('invoice_id', '=', self.id)]
        return action
    
    
    def sent_sms_smartbutton(self):

        return True
    def send_sms(self, sms_type = False):
        
        self_obj = self

        token = self.env['webto.sms.token'].search([('id', '>', 0)])
        if sms_type:
            value_sms = self.env['webto.sms.value'].search([('id', '>', 0), ('name', '=', sms_type)])
            
            sms_send = False
            if len(token) == 1: 
                sms_send = True
            else:
                sms_send = False
                raise ValidationError(u'Зөвхөн нэг л токен бүртгэлтэй байх ёстой.')

            if len(value_sms) == 1: 
                sms_send = True
            else:
                sms_send = False
                raise ValidationError(u'Зөвхөн нэг л утга бүртгэлтэй байх ёстой.')
               
            amount_due = 0
            sms_name = ''

            if sms_send == True:
                
                if self_obj.partner_id.sms_number:    
                    
                    sms_name = sms_type               
                    key1 = value_sms.key1
                    key2 = value_sms.key2
                    key3 = value_sms.key3
                    key4 = value_sms.key4
                    send_text = str(str(key1) +' '+ str(self_obj.partner_id.sms_send_name) +' '+ str(key2)+' ' + str(self_obj.invoice_date)+' ' + str(key3) +' '+ str(self_obj.amount_residual) +' ' + str(key4))
                   
                    new_text = re.sub(u" ", "%20", send_text)
                    if len(new_text) > 250:
                        raise ValidationError((u'Анхааруулга!' 'Таны мэссэжний урт 160 тэмдэгтээс урт байна.'))
                   
                    send_url = ('http://web2sms.skytel.mn/apiSend?token='+token.token+'&sendto='+self_obj.partner_id.sms_number+'&message='+new_text)
                    response_skytel = urlopen(send_url)
                    response_skytel.info()
                    data = response_skytel.read()
                    response_skytel.close()
                    
                    new_data = json.loads(data)
                   
                    if new_data['status'] == 1:
                        send_value1 = {
                            'state': 'success',
                            'name': sms_name,
                            'invoice_id': self_obj.id,
                            'date': datetime.now(),
                            'partner_id': self_obj.partner_id.id,
                            'sms_number': self_obj.partner_id.sms_number,
                            'user_id': self.env.user.id,
                            'sms_value': send_text,
                            }
                        self.env['web.to.sms'].create(send_value1)
                    else:
                        raise ValidationError((u'Илгээлт амжилтгүй! Та систем админтай холбогдоно уу...'))

                else:
                    raise ValidationError((u'Анхааруулга! Мэссэж илгээх дугаар тодорхойгүй байна.'))
        else:
            value_rent = self.env['webto.sms.value'].search([('id', '>', 0), ('name', '=', 'rent')])
            value_sale = self.env['webto.sms.value'].search([('id', '>', 0), ('name', '=', 'sale')])
            
            sms_send = False
            
            if len(token) == 1: 
                sms_send = True
            else:
                sms_send = False
                raise ValidationError(u'Зөвхөн нэг л токен бүртгэлтэй байх ёстой.')

            if len(value_rent) == 1: 
                sms_send = True
            else:
                sms_send = False
                raise ValidationError(u'Зөвхөн нэг л утга бүртгэлтэй байх ёстой.')
            
            if len(value_sale) == 1: 
                sms_send = True
            else:
                sms_send = False
                raise ValidationError(u'Зөвхөн нэг л утга бүртгэлтэй байх ёстой.')
            
            # token_objs = self.env['webto.sms.token'].browse(token)
            # value_rent_objs = self.env['webto.sms.value'].browse(value_rent)
            # value_sale_objs = self.env['webto.sms.value'].browse(value_sale)
            
            categ = 74
            amount_due = 0
            sms_name = ''

            if sms_send == True:
                
                if self_obj.partner_id.sms_number:    
                    if categ in self_obj.partner_id.category_id.ids:
                        key1 = value_rent.key1
                        key2 = value_rent.key2
                        key3 = value_rent.key3
                        key4 = value_rent.key4
                        sms_name = 'rent'
                    else:
                        sms_name = 'sale'               
                        key1 = value_sale.key1
                        key2 = value_sale.key2
                        key3 = value_sale.key3
                        key4 = value_sale.key4
                    send_text = str(str(key1) +' '+ str(self_obj.partner_id.sms_send_name) +' '+ str(key2)+' ' + str(self_obj.invoice_date)+' ' + str(key3) +' '+ str(self_obj.amount_residual) +' ' + str(key4))
                   
                    new_text = re.sub(u" ", "%20", send_text)
                    if len(new_text) > 250:
                        raise ValidationError((u'Анхааруулга!' 'Таны мэссэжний урт 160 тэмдэгтээс урт байна.'))
                    
                    send_url = ('http://web2sms.skytel.mn/apiSend?token='+token.token+'&sendto='+self_obj.partner_id.sms_number+'&message='+new_text)
                    response_skytel = urlopen(send_url)
                    response_skytel.info()
                    data = response_skytel.read()
                    response_skytel.close()
                    
                    new_data = json.loads(data)
                    if new_data['status'] == 1:
                        send_value1 = {
                            'state': 'success',
                            'name': sms_name,
                            'invoice_id': self_obj.id,
                            'date': datetime.now(),
                            'partner_id': self_obj.partner_id.id,
                            'sms_number': self_obj.partner_id.sms_number,
                            'user_id': self.env.user.id,
                            'sms_value': send_text,
                            }
                        self.env['web.to.sms'].create(send_value1)
                    else:
                        raise ValidationError((u'Илгээлт амжилтгүй! Та систем админтай холбогдоно уу...'))

                else:
                    raise ValidationError((u'Анхааруулга! Мэссэж илгээх дугаар тодорхойгүй байна.'))