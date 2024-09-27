import logging
from urllib.request import urlopen
import re
from datetime import datetime
import simplejson as json

from odoo import models, fields, _
from odoo.tools import populate
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _sms_count(self):
        res = {}
        for obj in self:
            obj_ids = self.env['web.to.sms'].search([('partner_id', '=', obj.id)])
            self.sms_count = len(obj_ids)

    sms_number = fields.Char(string='SMS number', size=8)
    sms_send_name = fields.Char(string='SMS name')
    sms_count = fields.Integer(compute='_sms_count', string='Sms', type='integer')

    def action_sended_sms(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('dakal_account.action_web_to_sms_tree')
        action['context'] = {}
        action['domain'] = [('partner_id', '=', self.id)]
        return action


    def send_sms_partner(self, sms_type = False):
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
            
            categ = 74
            amount_due = 0
            sms_name = ''
            if sms_send == True:
                if self_obj.sms_number:
                    
                    key1 = value_sms.key1
                    key2 = value_sms.key2
                    key3 = value_sms.key3
                    key4 = value_sms.key4
                    sms_name = sms_type
                    if self_obj.total_due > 0:
                        amount_due = self_obj.total_due
                    else:
                        for invoice in self_obj.total_invoiced:
                            if invoice.state == 'posted' and invoice.payment_state !='paid':
                                amount_due += invoice.amount_residual
                    send_text = str(str(key1) + str(self_obj.sms_send_name) + str(key2) + str(datetime.now().strftime('%Y-%m-%d')) + str(key3) + str(amount_due)  + str(key4))
                    new_text = re.sub(u" ", "%20", send_text)
                    
                    # if len(new_text) > 250:
                    #     raise ValidationError((u'Анхааруулга!' 'Таны мэссэжний урт 160 тэмдэгтээс урт байна.'))
                    send_url = ('http://web2sms.skytel.mn/apiSend?token='+token.token+'&sendto='+self_obj.sms_number+'&message='+new_text)
                    response_skytel = urlopen(send_url)
                    response_skytel.info()
                    data = response_skytel.read()
                    response_skytel.close()

                    new_data = json.loads(data)
                    if new_data['status'] == 1:
                        send_value1 = {
                            'state': 'success',
                            'name': sms_name,
                            'date': datetime.now(),
                            'partner_id': self_obj.id,
                            'sms_number': self_obj.sms_number,
                            'user_id': self.env.user.id,
                            'sms_value': send_text,
                            }
                        self.env['web.to.sms'].create(send_value1)
        #                         raise osv.except_osv((u'Амжилттай илгээгдлээ.!'), send_text)
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
                if self_obj.sms_number:
                    if categ in self_obj.category_id.ids:
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
                    if self_obj.total_due > 0:
                        amount_due = self_obj.total_due
                    else:
                        for invoice in self_obj.total_invoiced:
                            if invoice.state == 'posted' and invoice.payment_state !='paid':
                                amount_due += invoice.amount_residual
                    send_text = str(str(key1) + str(self_obj.sms_send_name) + str(key2) + str(datetime.now().strftime('%Y-%m-%d')) + str(key3) + str(amount_due)  + str(key4))
                    new_text = re.sub(u" ", "%20", send_text)
                    
                    # if len(new_text) > 250:
                    #     raise ValidationError((u'Анхааруулга!' 'Таны мэссэжний урт 160 тэмдэгтээс урт байна.'))
                    send_url = ('http://web2sms.skytel.mn/apiSend?token='+token.token+'&sendto='+self_obj.sms_number+'&message='+new_text)
                    response_skytel = urlopen(send_url)
                    response_skytel.info()
                    data = response_skytel.read()
                    response_skytel.close()

                    new_data = json.loads(data)
                    if new_data['status'] == 1:
                        send_value1 = {
                            'state': 'success',
                            'name': sms_name,
                            'date': datetime.now(),
                            'partner_id': self_obj.id,
                            'sms_number': self_obj.sms_number,
                            'user_id': self.env.user.id,
                            'sms_value': send_text,
                            }
                        self.env['web.to.sms'].create(send_value1)
        #                         raise osv.except_osv((u'Амжилттай илгээгдлээ.!'), send_text)
                    else:
                        raise ValidationError((u'Илгээлт амжилтгүй! Та систем админтай холбогдоно уу...'))

                else:
                    raise ValidationError((u'Анхааруулга! Мэссэж илгээх дугаар тодорхойгүй байна.'))