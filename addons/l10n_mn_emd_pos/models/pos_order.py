# -*- coding: utf-8 -*-

import json
import logging
import requests
import time
from datetime import date, datetime
from time import mktime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"
    
    detail_id = fields.Integer('EMD detail id')

class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    receipt_number = fields.Char('EMD receiptNumber')
    last_name =  fields.Char('Last Name')
    first_name = fields.Char('First Name')
    register =  fields.Char('Register No')
    receipt_id = fields.Char('Receipt Id')
    prescriptionType = fields.Integer(string='Prescription Type')
    receipt_bill_id = fields.Char('Receipt\'s Bill Id')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        if 'register' in ui_order.keys():
            receipt_number =  ui_order['receipt_number']
            last_name =  ui_order['last_name']
            first_name =  ui_order['first_name']
            register =  ui_order['register']
            receipt_id =  ui_order['receipt_id']
            prescriptionType = ui_order['prescriptionType']
            order_fields.update({'receipt_number': receipt_number,
                                'last_name': last_name,
                                'first_name': first_name,
                                'register': register,
                                'receipt_id': receipt_id,
                                'prescriptionType': prescriptionType,
                                 })
        return order_fields
    
    @api.model
    def get_emd_discount(self, json_data):
        data = json.loads(json_data)
        price = data['price']
        qty = data['quantity']
        pid = data['productId']
        pl_id = data['pricelist_id']
        discount = 0
        # product_pl_obj = self.env['product.pricelist']
        product_obj = self.env['product.product']
        # product_pli_obj = self.env['product.pricelist.item']
        
        # pricelist = product_pl_obj.browse(pl_id)
        product = product_obj.search([('id', '=', pid)])
        # pli = product_pli_obj.search([('pricelist_id', '=', pl_id), ('product_tmpl_id', '=', product.product_tmpl_id.id)], order='id DESC', limit=1)
        # max_price = product.emd_insurance_list_id.tbltMaxPrice
        # em_price = pricelist.price_get(pid, qty)

        if product.emd_insurance_list_id: 
            discount = product.emd_insurance_list_id.tbltUnitDisAmt * 100 / product.emd_insurance_list_id.tbltUnitPrice
        # if max_price == 0:
        if int(product.package_qty) > 0:
            max_price = product.emd_insurance_list_id.tbltUnitPrice * int(product.package_qty)
    
        res = {
            'emd_discount': discount,
            'max_price': max_price,
            'product_name': product.name,
            'qty': qty
        }
        return res

    @api.model
    def check_connection(self):
        '''
        Интернет холболт байгаа эсэхийг шалгахад ашиглах функц
        '''
        return True
    def get_access_token(self, config):
        head = {'Authorization': 'Basic VV9mZl05Qmp5WlhMbUcmZHcmOlo3JHtFenlyRDRheUN9RkxkJg=='}
        data = {
            'grant_type': 'password',
            'username': 'aptk0010', # config.user_name, # 
            'password':  '9875321', # config.password #
        }
        emd_url = 'https://st.health.gov.mn/oauth/token?'
        response = requests.post(emd_url, params=data, headers=head, verify=False)
        
        if response.status_code == 200:
            new_data = json.loads(response.text)
            access_token = new_data['access_token']
        else:
            error_message = u'ЭМД-ийн системтэй холбогдоход алдаа гарлаа'
            _logger.error(u'Аccess token авахад алдаа гарлаа. %s', data)

        return  access_token,
          
    @api.model
    def check_number(self, regNumber, check_number, pos_id):
        '''
        ЭМД -ын цахим системээс токен авч жорын дугаараар шалгах функц
        '''
        recipt_data = {}
        json_data = []
        access_token = ''
        error_message = ''
        conf_obj = self.env['pos.config']
        config = conf_obj.browse(pos_id)
        
        access_token = self.get_access_token(config)[0]
        recipt_data = self.check_reciept(access_token, regNumber, check_number)
        json_data = json.dumps(recipt_data)
        
        return {
            'error_message': error_message,
            'access_token': access_token,
            'json_data': json_data,
        }

    @api.model
    def check_reciept(self, token, regNumber, check_number):
        '''
        ЭМД -ын цахим системээс авсан токеноор жорын мэдээлэл авах функц
        '''
        myUrl = 'https://st.health.gov.mn/eins/prescription/getPrescription?access_token='+ token
        data = {'receiptNumber': check_number,
                'regNo': regNumber }
    
        head = {"Content-Type": "application/json; charset=utf-8"}
        json_data = json.dumps(data)
        try:
            response = requests.post(myUrl, headers=head, data=json_data, verify=False)
            
        except requests.exceptions.HTTPError as err:
            print('HTTP error occurred:', err)
        except Exception as e:
            print('An unexpected error occurred:', e)
        new_data = []
        if response.status_code == 200:
            if response.text:
                new_data = json.loads(response.text)
        else:
            _logger.error(u'Жорын мэдээлэл авахад алдаа гарлаа. %s', data)
            

        if new_data:        
            return new_data

    def check_emd_receipt(self):
        '''
        ЭМД -ын цахим системд илгээсэн жорын мэдээлэл шалгах функц
        '''
        
        config = self.session_id.config_id
        access_token = self.get_access_token(config)[0]

        myUrl = 'https://st.health.gov.mn/eins/prescription/checkPosRno?access_token='+ access_token
        data = {
                'posRno': self.receipt_bill_id
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
        
    def generate_order_json(self):
        data = {}

        data['totalAmount'] = round(self.amount_total, 2)
        data['totalVat'] = round((self.amount_total - self.amount_total/1.1), 2)
        data['totalCityTax'] = round(self.amount_tax_city, 2)
        data['districtCode'] = self.session_id.config_id.aimag_district_id.code or self.env['ebarimt.aimag.district'].search([('name','ilike',self.env.user.company_id.state_id.name)]).code
        data['merchantTin'] = self.session_id.config_id.merchant_tin
        data['posNo'] = (self.session_id.config_id.pos_no or str(1)).zfill(4)
        data['type'] = self.bill_type
        data['branchNo'] = (self.session_id.config_id.branch_no or str(1)).zfill(3)
        data['date'] = (fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return data

    def generate_order_line_json(self, order_line):

        items = {}
        emd_datas = {}
        ins_list = order_line.product_id.emd_insurance_list_id
        qty = order_line.qty * order_line.product_id.package_qty
        '''
        Даатгалтай болон энгийн жороос хамаарч даатгалын дүнг тооцоолох
        '''
      
        if order_line.order_id.prescriptionType == 1:
            insAmt = ins_list.tbltUnitDisAmt * qty
        else:
            insAmt = 0
        emd_datas['insAmount']= insAmt 
        emd_datas['detailId']= order_line.detail_id 
        emd_datas['tbltId']= ins_list.tbltId
                 
        prod_name = order_line.product_id.with_context({'lang': 'mn_MN'}).name
        items['name'] = prod_name
        if order_line.product_id.emd_insurance_list_id:
            items['barCode'] = order_line.product_id.emd_insurance_list_id.tbltBarCode
        else:
            items['barCode'] = order_line.product_id.barcode
        if not order_line.product_id.barcode or len(order_line.product_id.barcode) < 13 :
            items['barCodeType'] = 'UNDEFINED'
            items['barCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        else:
            items['barCodeType'] = 'GS1'
        items['classificationCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        items['measureUnit'] = order_line.product_id.uom_id.name
        if ins_list:
            items['qty'] = qty
            items['unitPrice'] = ins_list.tbltUnitPrice
        else:
            items['qty'] = order_line.qty
            items['unitPrice'] = order_line.price_unit
        
        items['totalCityTax'] = order_line.amount_tax_city
        items['totalAmount'] = order_line.price_subtotal_incl
        items['totalVAT'] = round((order_line.price_subtotal_incl -  order_line.price_subtotal_incl/1.1),2)
        items['data'] = emd_datas
       
        return items


    def send_ebarimt(self):
        order_json = self.generate_order_json()
        order_lines = []
        emd_data = {}
        receipt = {}
        totalInsAmt = 0
        receipts = []
        payment = {}
        payments = []
        
        for line in self.lines:
            if line.product_id.code:
                order_lines.append(self.generate_order_line_json(line))

                ins_list = line.product_id.emd_insurance_list_id
                qty = line.qty * line.product_id.package_qty
                '''
                Даатгалтай болон энгийн жороос хамаарч Даатгалын дүнг тооцоолох
                '''
                
                if line.order_id.prescriptionType == 1:
                    insAmt = ins_list.tbltUnitDisAmt * qty
                else:
                    insAmt = 0
                
                totalInsAmt += insAmt
             
                if line.product_id.emd_insurance_list_id.tbltManufacture:
                    receipt['merchantTin'] = self.session_id.config_id.novartis_merchant_tin
                    order_json['type']='B2C_INVOICE'
                    
                    qty = line.qty * line.product_id.package_qty
                    total_price = line.product_id.emd_insurance_list_id.tbltUnitPrice * qty
                    tax_amount = total_price - total_price /1.1
                   
                    order_json['totalAmount'] = round(total_price, 2)
                    receipt['totalAmount'] = round(total_price, 2)
                    order_json['totalVat'] = round(tax_amount, 2)
                    receipt['totalVat'] = round(tax_amount, 2)
                else:
                    receipt['merchantTin'] = self.session_id.config_id.merchant_tin
                    receipt['totalAmount'] = round(self.amount_total, 2)
                    receipt['totalVat'] = round((self.amount_total - self.amount_total/1.1), 2)

        ###################### Receipts list #################
        receipt['items'] = order_lines

        emd_data['receiptId'] = self.receipt_id
        emd_data['receiptNumber'] = self.receipt_number
        emd_data['insAmount'] = totalInsAmt
        emd_data['paidAmount'] = self.amount_total
        emd_data['buyType'] = 1
        emd_data['reason'] = ''
        emd_data['buyerId'] = self.register
        emd_data['issuerId'] = ''
        receipt['totalCityTax'] = round(self.amount_tax_city, 2)
        receipt['taxType'] = self.tax_type
        receipt['data'] = emd_data
        receipts.append(receipt)
        order_json['receipts'] = receipts

        ###################### Payments list #################
        
        for p in self.payment_ids:
            data = {}
            data['approvalCode'] = "123456"
            data['rrn'] = "123456789456"
            data['date'] = (fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if p.payment_method_id.is_cash_count:
                payment['code'] = "CASH"
                payment['paidAmount'] = round(p.amount, 2)
                payment['status'] = "PAID"
                payment['data'] = data
            else:
                payment['code'] = "PAYMENT_CARD"
                payment['paidAmount'] = round(p.amount, 2)
                payment['status'] = "PAID"
                payment['data'] = data
            payments.append(payment)
        order_json['payments'] = payments

        access_token = self.get_access_token(self.session_id.config_id)[0]
        query_params = {
            'access_token':[access_token]
            }
        exchange_data = {
            "ЭМД-н систем рүү жорын мэдээлэл илгээх":{
                "queryParams": query_params
            }
        }
        order_json['exchangeData'] = exchange_data
        ###################### GetInformation #################

        info_url = "http://" +self.session_id.config_id.ebarimt_service_host +':'+ self.session_id.config_id.ebarimt_service_port+"/rest/info"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.get(url=info_url, headers=headers)
        if response:
            try:
                res = json.loads(response.text)
                
            except Exception as e:
                _logger.error(e)
        ###################### SendData #################
         
        ebarimt_url = "http://" + self.session_id.config_id.ebarimt_service_host +':'+ self.session_id.config_id.ebarimt_service_port+'/rest/receipt'
        headers = {"Content-Type": "application/json; charset=utf-8"}
        
        self.note = order_json
        response = requests.post(url=ebarimt_url, headers=headers, json=order_json)
        if response.text:
            
            try:
                data = json.loads(response.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            if data['status'] == 'ERROR':
                raise ValidationError(data['message'])

        
        if data:
            self.bill_id = data['id']
            self.receipt_bill_id = data['receipts'][0]['id']
            self.bill_printed_date = fields.Datetime.from_string(data['date'])
            insurance_id = False
          
            insurance_obj = self.env['emd.insurance.sale']
            insuranceLine_obj = self.env['emd.insurance.sale.line']
            invoice_obj = self.env['account.move']
           
            product_obj = self.env['product.product']
            config = self.session_id.config_id
            if data['receipts'][0]['data']['receiptNumber']:
                vals = {
                    'name': data['receipts'][0]['data']['receiptNumber'],
                    'date': fields.Datetime.from_string(data['date']),
                    'totalAmt': data['receipts'][0]['totalAmount'],
                    'insAmt': data['receipts'][0]['data']['insAmount'],
                    'lastName': self.last_name,
                    'firstName': self.first_name,
                    'register': data['receipts'][0]['data']['buyerId'],
                    'partner_id': config.emd_partner_id.id,
                    'origin': self.id,
                    'state': 'sented',
                    'netAmt': data['receipts'][0]['data']['paidAmount'],
                    'vatAmt': data['receipts'][0]['totalVAT'],
                    'ddtd': data['posNo'],
                    'receipt_id': self.receipt_id,
                    'config_id': config.id,
                   
                }
                if data['receipts'][0]['data']['insAmount']>0:
                    vals['receipt_type'] = 'insurance'
                
                insurance_id = insurance_obj.create(vals)
       
                if insurance_id:
                    for details in order_json['receipts'][0]['items']:
                        product = product_obj.search([('name', '=', details['name'])])
                        lvals = {
                            'parent_id': insurance_id.id,
                            'detail_id': details['data']['detailId'],
                            'product_id': product.id,
                            'quantity': details['qty'],
                            'insAmt': details['data']['insAmount'],
                            'price': details['unitPrice'],
                            'totalAmt': details['totalAmount'],
                        }
                        
                        insurance_line = insuranceLine_obj.create(lvals)
            return data
