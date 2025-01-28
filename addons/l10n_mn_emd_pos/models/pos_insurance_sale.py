# -*- coding: utf-8 -*-
# import json
import logging
import requests
from datetime import datetime
from time import mktime
import simplejson as json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError  # @UnresolvedImport

_logger = logging.getLogger(__name__)


class PosInsuranceSale(models.Model):
    _name = "emd.insurance.sale"
    _order = "date desc, id desc"
    _description = "POS sale order Health Insurance"

    name = fields.Char('Reciept Number', required=True)
    date = fields.Datetime('Date')
    totalAmt = fields.Float('Total Amount')
    insAmt = fields.Float('Insurance Amount')
    vatAmt = fields.Float('Vat Amount')
    netAmt = fields.Float('Net Amount')
    lastName = fields.Char('Last Name')
    firstName = fields.Char('First Name')
    register = fields.Char('Register Number', required=True)
    detCnt =  fields.Integer('detCnt')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sented', 'Sented')], default="draft")
    insurance_line = fields.One2many('emd.insurance.sale.line', 'parent_id', 'Line')
    origin = fields.Many2one('pos.order', string='Origin')
    partner_id = fields.Many2one('res.partner', string='Partner')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    ddtd = fields.Char('Unique Number')
    config_id = fields.Many2one('pos.config', string='POS Configure', required=True)
    receipt_id = fields.Integer('Receipt ID')
    receipt_type = fields.Selection([
        ('simple', 'Simple'),
        ('insurance', 'Insurance'),], string='Reciept type', default='simple',)
    
    def action_draft(self):
        self.write({
                  'state':'draft'
                  })
  
    def check_emd_receipt(self):
        '''
        ЭМД -ын цахим системд илгээсэн жорын мэдээлэл шалгах функц
        '''
        
        config = self.config_id
        access_token = self.origin.get_access_token(config)[0]

        myUrl = 'https://health.gov.mn/eins/prescription/checkPosRno?access_token='+ access_token
        data = {
                'posRno': self.origin.receipt_bill_id
                }
    
        head = {"Content-Type": "application/json; charset=utf-8"}
        json_data = json.dumps(data)
        response = requests.post(myUrl, headers=head, data=json_data, verify=False)
        
        res = []
        if response.status_code == 200:
            if response.text:
                res = json.loads(response.text)

        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        if res['code']==200:
            
            context['message']= (u'Тайлбар: %s, \n Жорын дугаар: %s, \n  Борлуулсан огноо: %s, \n  Эмийн сан: %s, \n  Төлөв: %s, \n  Даатгалын дүн: %s') %(
                res['description'], res['result'][0]['receiptNumber'], res['result'][0]['salesDate'],res['result'][0]['hospitalName'], 
                res['result'][0]['checkStatus'], res['result'][0]['insAmt'],)
            
        elif res['code'] == 400:
            context['message']= ('Code: %s, Description: %s,' ) %(res['code'], res['description'])
        return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }
        


class PosInsuranceSaleLine(models.Model):
    _name = "emd.insurance.sale.line"
    _description = "POS sale order line Health Insurance"

    product_id = fields.Many2one('product.product', 'Product Name')
    quantity = fields.Float('Quantity')
    price = fields.Float('Price')
    totalAmt = fields.Float('Total Amount')
    insAmt = fields.Float('Insurance Amount')
    parent_id = fields.Many2one('emd.insurance.sale', 'Parent')
    detail_id = fields.Integer('Detail ID')
    intern_name = fields.Char('International Name')
    date = fields.Datetime('Date', related='parent_id.date', readonly=True)
    config_id = fields.Many2one(string='POS Configure', related='parent_id.config_id', readonly=True)
    product_category_id = fields.Many2one(string='POS Configure', related='product_id.categ_id', readonly=True)
    tbltId = fields.Integer('Tablet ID')
    packGroup = fields.Integer('packGroup')

