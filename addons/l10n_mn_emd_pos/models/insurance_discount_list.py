# -*- coding: utf-8 -*-
import json
import logging
import requests
import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError  # @UnresolvedImport
_logger = logging.getLogger(__name__)

class InsuranceDiscountList(models.Model):
    _name = "emd.insurance.discount.list"
    _description = "Mongolian Health Insurance Discount List"

    tbltId = fields.Integer('EMD ID', readonly=True, store=True)
    tbltNameMon = fields.Char('Mon Name', readonly=True, store=True)
    tbltNameInter = fields.Char('Inter Name', readonly=True, store=True)
    tbltNameSales = fields.Char('Sales Name', readonly=True, store=True)
    tbltType = fields.Char('tbltT ype', readonly=True, store=True)
    tbltSizeUnit = fields.Char('tblt Size Unit', readonly=True, store=True)
    tbltSizeMixture = fields.Char('tblt Size Mixture', readonly=True, store=True)
    tbltBarCode = fields.Char('BarCode')
    tbltIsDiscount = fields.Boolean('tblt Is Discount', readonly=True, store=True)
    status = fields.Char('Status', readonly=True, store=True)
    tbltTypeName = fields.Char('tblt Type Name', store=True)
    tbltGroup = fields.Integer('tbltGroup', store=True)
    tbltSCode = fields.Integer('tbltSCode', store=True)
    groupName = fields.Char('Group Name', store=True)
    packGroup = fields.Integer('EMD Group Id', readonly=True, store=True)
    tbltUnitDisAmt = fields.Float('Discount Unit Amount')
    tbltUnitPrice = fields.Float('Unit Price', readonly=True, store=True)
    isBc = fields.Boolean('isBc')
    tbltManufacture = fields.Char('tblt Manufacture', readonly=True, store=True)
    
    product_ids =  fields.Many2many('product.template', 'product_temp_insurance_list_rel', 'product_id' 'insurance_list_id', string="Products")
   
    
    def write(self, vals):
        for product in self.product_ids:
            product.write({'emd_insurance_list_id': self.id})
        return super(InsuranceDiscountList, self).write(vals)
    
    @api.depends('tbltNameSales')
    def name_get(self):
        result = []
        for insurance_list in self:
            if insurance_list.tbltSizeMixture:
                
                name = insurance_list.tbltNameSales + ' '+ insurance_list.tbltSizeMixture
            else:
                name = insurance_list.tbltNameSales 
            result.append((insurance_list.id, name))
        return result
    
    def get_insurense_list(self):
        access_token = None
        list_obj = self.env['emd.insurance.discount.list']
        pos_conf_obj = self.env['pos.config']
        config_ids = pos_conf_obj.search([('user_name','!=', False)])[0]
        token_head = {'Authorization': 'Basic VV9mZl05Qmp5WlhMbUcmZHcmOlo3JHtFenlyRDRheUN9RkxkJg=='}
        token_data = {
                'grant_type': 'password',
                'username': config_ids.user_name,
                'password': config_ids.password,
                }
        token_url = 'https://health.gov.mn/oauth/token?'
        token_response = requests.post(token_url, params=token_data, headers=token_head, verify=False)
        if token_response.status_code == 200:
            new_data = json.loads(token_response.text)
            access_token = new_data['access_token']
            _logger.info(u'ЭМД-н системээс авсан токен %s' % (access_token))
        else: 
            error_message = u'ЭМД-ийн системтэй холбогдоход алдаа гарлаа'
            _logger.error(u'Аccess token авахад алдаа гарлаа.')
            raise ValidationError(u'ЭМД системтэй холбогдож чадсангүй!')
         
        url = 'https://health.gov.mn/eins/prescription/getTabletFindAll?page=1&size=1000&type=1&access_token='+ access_token
        head = {"Content-Type": "application/json"}
        params = {'field':None,
                  'value':None,
                  'type':None,
                  "order":None,
                  "dir":None }
        datas = json.dumps(params)
        response = requests.post(url, headers=head, data=datas, verify=False)

        if response.status_code == 200:
            insurancce_data = json.loads(response.text)
            # self._cr.execute(""" DELETE FROM emd_insurance_discount_list """)
            for tbltData in insurancce_data['data']:
                
                _logger.info(u'ЭМД-н системээс авсан data tbltUnitPrice %s' % (tbltData['tbltUnitPrice']))
                list_id =  self.env['emd.insurance.discount.list'].search([('tbltId', '=', tbltData['id'])])
                if list_id:       
                    list_id[0].write({
                        'tbltNameMon': tbltData['tbltNameMon'],
                        'tbltNameInter': tbltData['tbltNameInter'],
                        'tbltNameSales': tbltData['tbltNameSales'],
                        'tbltType': tbltData['tbltType'],
                        'tbltSizeUnit': tbltData['tbltSizeUnit'],
                        'tbltSizeMixture': tbltData['tbltSizeMixture'],
                        'tbltBarCode': tbltData['tbltBarCode'],
                        'tbltIsDiscount': tbltData['tbltIsDiscount'],
                        'status': tbltData['status'],
                        'tbltTypeName': tbltData['tbltTypeName'],
                        'tbltGroup': tbltData['tbltGroup'],
                        'tbltSCode': tbltData['tbltSCode'],
                        'groupName': tbltData['groupName'],
                        'packGroup': tbltData['packGroup'],
                        'tbltUnitDisAmt': float(tbltData['tbltUnitDisAmt'] or 0),
                        'tbltUnitPrice': float(tbltData['tbltUnitPrice']),
                        'isBc': tbltData['isBc'],
                        'tbltManufacture': tbltData['tbltManufacture'],
                        })
                else:
                    discount = 0
                    if float(tbltData['tbltUnitPrice'])>0:
                        discount = float(tbltData['tbltUnitDisAmt'])*100/float(tbltData['tbltUnitPrice'])
                    vals = {
                        'tbltId': tbltData['id'],
                        'tbltNameMon': tbltData['tbltNameMon'],
                        'tbltNameInter': tbltData['tbltNameInter'],
                        'tbltNameSales': tbltData['tbltNameSales'],
                        'tbltType': tbltData['tbltType'],
                        'tbltSizeUnit': tbltData['tbltSizeUnit'],
                        'tbltSizeMixture': tbltData['tbltSizeMixture'],
                        'tbltBarCode': tbltData['tbltBarCode'],
                        'tbltIsDiscount': tbltData['tbltIsDiscount'],
                        'status': tbltData['status'],
                        'tbltTypeName': tbltData['tbltTypeName'],
                        'tbltGroup': tbltData['tbltGroup'],
                        'tbltSCode': tbltData['tbltSCode'],
                        'groupName': tbltData['groupName'],
                        'packGroup': tbltData['packGroup'],
                        'tbltUnitDisAmt': float(tbltData['tbltUnitDisAmt'] or 0),
                        'tbltUnitPrice': float(tbltData['tbltUnitPrice']),
                        'isBc': tbltData['isBc'],
                        'tbltManufacture': tbltData['tbltManufacture'],
                        }
                    list_obj.create(vals)
        else:
            error_message = u'ЭМД-ийн системтэй холбогдоход алдаа гарлаа'
            _logger.error(u'Аccess token авахад алдаа гарлаа.')
            raise ValidationError(u'ЭМД системтэй холбогдож чадсангүй!')
        return True   