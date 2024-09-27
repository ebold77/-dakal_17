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

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        if 'register' in ui_order.keys():
            receipt_number =  ui_order['receipt_number']
            last_name =  ui_order['last_name']
            first_name =  ui_order['first_name']
            register =  ui_order['register']
            receipt_id =  ui_order['receipt_id']
            order_fields.update({'receipt_number': receipt_number,
                                'last_name': last_name,
                                'first_name': first_name,
                                'register': register,
                                'receipt_id': receipt_id
                                 })
        return order_fields
    
    @api.model
    def get_emd_discount(self, json_data):
        data = json.loads(json_data)
        price = data['price']
        qty = data['quantity']
        pid = data['productId']
        pl_id = data['pricelist_id']
        # product_pl_obj = self.env['product.pricelist']
        product_obj = self.env['product.product']
        # product_pli_obj = self.env['product.pricelist.item']
        
        # pricelist = product_pl_obj.browse(pl_id)
        product = product_obj.search([('id', '=', pid)])
        # pli = product_pli_obj.search([('pricelist_id', '=', pl_id), ('product_tmpl_id', '=', product.product_tmpl_id.id)], order='id DESC', limit=1)
        # max_price = product.insurance_list_id.tbltMaxPrice
        # em_price = pricelist.price_get(pid, qty)
        discount = product.insurance_list_id.tbltUnitDisAmt * 100 / product.insurance_list_id.tbltUnitPrice
        # if max_price == 0:
        max_price = price
        print('price===========', price)
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
    def get_access_token(self):
        head = {'Authorization': 'Basic VV9mZl05Qmp5WlhMbUcmZHcmOlo3JHtFenlyRDRheUN9RkxkJg=='}
        data = {
            'grant_type': 'password',
            'username': 'aptk0010', #config_ids.user_name,
            'password': '9875321', # config_ids.password,
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
        
        access_token = self.get_access_token()[0]
        print('access_token===>>', access_token)
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
        print('my url==========', myUrl, data, type(data))
        json_data = json.dumps(data)
        try:
            response = requests.post(myUrl, headers=head, data=json_data, verify=False)
            print('res===========', response.status_code, response.text)
            # response.raise_for_status()
            
        except requests.exceptions.HTTPError as err:
            print('HTTP error occurred:', err)
        except Exception as e:
            print('An unexpected error occurred:', e)
        new_data = []
        if response.status_code == 200:
            if response.text:
                new_data = json.loads(response.text)

                if new_data['result']['status']==3:
                    raise ValidationError(u'Худалдаж авсан жор тул борлуулалт хийх боломжгүй')
                elif new_data['result']['status']==5:
                    raise ValidationError(u'Хугацаа дууссан жор тул борлуулалт хийх боломжгүй')
        else:
            _logger.error(u'Жорын мэдээлэл авахад алдаа гарлаа. %s', data)
            

        if new_data:
            # if new_data['prescriptionType']==2 or new_data['prescriptionType']:
                 
            return new_data
        
    def generate_order_json(self):
        data = {}
        data['totalAmount'] = round(self.amount_total, 2)
        data['totalVat'] = round(self.amount_tax_vat, 2)
        data['totalCityTax'] = round(self.amount_tax_city, 2)
        data['districtCode'] = self.session_id.config_id.aimag_district_id.code or self.env['ebarimt.aimag.district'].search([('name','ilike',self.env.user.company_id.state_id.name)]).code
        data['merchantTin'] = self.session_id.config_id.merchant_tin
        data['posNo'] = (self.session_id.config_id.pos_no or str(1)).zfill(4)
        data['type'] = self.bill_type
        data['branchNo'] = (self.session_id.config_id.branch_no or str(1)).zfill(3)
        data['date'] = (fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print('oder json data------------>>', data)
        return data

    def generate_order_line_json(self, order_line):
        print('eb json line price ===', order_line.price_unit, order_line.product_id.id, order_line.product_id.name, 
              order_line.product_id.insurance_list_id.tbltNameSales, order_line.product_id.insurance_list_id.tbltBarCode)
        items = {}
        emd_datas = {}
        ins_list = order_line.product_id.insurance_list_id
        qty = order_line.qty * order_line.product_id.package_qty
        insAmt = (order_line.price_unit * order_line.discount/100) * order_line.qty
        emd_datas['insAmount']= insAmt 
        emd_datas['detailId']= order_line.detail_id 
        emd_datas['tbltId']= ins_list.tbltId 
        prod_name = order_line.product_id.with_context({'lang': 'mn_MN'}).name
        items['name'] = prod_name
        if order_line.product_id.insurance_list_id:
            items['barCode'] = order_line.product_id.insurance_list_id.tbltBarCode
        else:
            items['barCode'] = order_line.product_id.barcode
        if not order_line.product_id.barcode or len(order_line.product_id.barcode) < 13 :
            items['barCodeType'] = 'UNDEFINED'
            items['barCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        else:
            items['barCodeType'] = 'GS1'
        items['classificationCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        items['measureUnit'] = order_line.product_id.uom_id.name
        items['qty'] = qty
        items['unitPrice'] = ins_list.tbltUnitPrice
        
        items['totalCityTax'] = order_line.amount_tax_city
        if order_line.product_id.insurance_list_id.tbltManufacture:
            items['totalAmount'] = insAmt
            items['totalVAT'] = insAmt - insAmt/1.1
        else:
            items['totalAmount'] = order_line.price_subtotal_incl
            items['totalVAT'] = order_line.amount_tax_vat
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
                insAmt = (line.price_unit * line.discount/100) * line.qty
                totalInsAmt += insAmt
                if line.product_id.insurance_list_id.tbltManufacture:
                    receipt['merchantTin'] = self.session_id.config_id.novartis_merchant_tin
                    order_json['type']='B2C_INVOICE'
                    
                    qty = line.qty * line.product_id.package_qty
                    total_price = line.product_id.insurance_list_id.tbltUnitPrice * qty
                    tax_amount = total_price - total_price /1.1
                   
                    order_json['totalAmount'] = round(total_price, 2)
                    receipt['totalAmount'] = round(total_price, 2)
                    order_json['totalVat'] = round(tax_amount, 2)
                    receipt['totalVat'] = round(tax_amount, 2)
                else:
                    receipt['merchantTin'] = self.session_id.config_id.merchant_tin
                    receipt['totalAmount'] = round(self.amount_total, 2)
                    receipt['totalVat'] = round(self.amount_tax_vat, 2)
        print('order_lines', order_lines)
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

        access_token = self.get_access_token()[0]
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
        print('order_json====================>>', order_json)
        response = requests.post(url=ebarimt_url, headers=headers, json=order_json)
        if response.text:
            print('response==============>>>', response.text)
            try:
                data = json.loads(response.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            # data_json = json.dumps(data)
            if data['status'] == 'ERROR':
                raise ValidationError(data['message'])
        
        if data:
            self.bill_id = data['id']
            self.bill_printed_date = fields.Datetime.from_string(data['date'])
            insurance_id = False
            # config_id = pos_id
            # conf_obj = self.env['pos.config']
            insurance_obj = self.env['pos.insurance.sale']
            insuranceLine_obj = self.env['pos.insurance.sale.line']
            invoice_obj = self.env['account.move']
            # invoice_line_obj = self.env['account.move.line']
            product_obj = self.env['product.product']
            config = self.session_id.config_id
            print('data=============>>>', data, data['receipts'][0]['data']['receiptNumber'])
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
                # "detCnt": data['detCnt'],
            }
            insurance_id = insurance_obj.create(vals)
            # self._cr.execute("select id from account_move where partner_id = %s \
            #             and invoice_date = '%s' and journal_id = %s and state = 'draft'"
            #                 % (config.emd_partner_id.id, json_arg['salesDate'], config.invoice_journal_id.id))
            # fetch_inv_id = self._cr.fetchone()
            # if fetch_inv_id == [] or not fetch_inv_id:
            #     inv_id = invoice_obj.create(
            #         {
            #             'journal_id': config.invoice_journal_id.id,
            #             'invoice_date': json_arg['salesDate'],
            #             'company_id': config.company_id.id,
            #             'move_type': 'out_invoice',
            #             'state': 'draft',
            #             'partner_id': config.emd_partner_id.id,
            #         })
            # else:
            #     inv_id = invoice_obj.search([('id', '=', fetch_inv_id[0])])
            if insurance_id:
                for details in order_json['receipts'][0]['items']:
                    product = product_obj.search([('name', '=', details['name'])])
                    print('product=========?>>>', product)
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
    #                 if inv_id:
    #                     product = product_obj.search([('id', '=', details['product_id'])])
    #                     price_unit = float(details['insAmt']) / float(details['quantity'])
    #                     account_id = product.categ_id.property_account_income_categ_id.id,
    #                     invoice_line = {
    #                             'product_id': product.id,
    #                             'quantity': float(details['quantity']/product.package_qty),
    #                             'price_unit': float(details['insAmt']) / float(details['quantity']/product.package_qty),
    #                             'name': details['productName'],
    #                             'product_uom_id': product.uom_id.id,
    # #                             'move_id': inv_id.id,
    #                             'tax_ids': [(6, 0, product.taxes_id.ids)],
    #                             'account_id': account_id,
    #                         }
    #                     inv_id.write({'invoice_line_ids': [(0, None, invoice_line)]})
       

        return data
    
#     @api.model
#     def get_ebarimt(self, server_ids):
#         ebarimt_data = super(PosOrder, self).get_ebarimt(server_ids)
#         emdStocks= []
#         totalInsAmt = detCnt = 0
#         for s in server_ids:
#             order = self.env['pos.order'].browse(s['id'])
#             _logger.info(u'Жорын мэдээлэл : %s, %s,%s, %s, %s', order.last_name, order.first_name, order.register, order.receipt_number, order.receipt_id)
#             for line in order.lines:
#                 if line.detail_id:
#                     ins_list = line.product_id.insurance_list_id
#                     qty = line.qty * line.product_id.package_qty
#                     insAmt = (line.price_unit * line.discount/100) * line.qty
#                     emdStocks.append({
#                             "detailId": line.detail_id,
#                             "barCode": ins_list.tbltBarCode,
#                             "productName": ins_list.tbltNameSales+ ins_list.tbltSizeMixture,
#                             "quantity": qty,
#                             "insAmt": insAmt,
#                             "price": ins_list.tbltUnitPrice,
#                             "totalAmt": line.price_subtotal_incl,
#                             "tbltId":ins_list.tbltId,
#                             "packGroup": ins_list.packGroup,
#                             "status": 1,
#                             "product_id": line.product_id.id
#                         })
#                     detCnt += 1
#                     totalInsAmt += insAmt
                    
#                     _logger.info(u'Жорын мөрийн мэдээлэл : %s', emdStocks)
#             if order.lines[0].detail_id:    
#                 jsonData = {
#                         "posRno": order.bill_id,
#                         "salesDate": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
#                         "totalAmt": order.amount_total + totalInsAmt,    # order.get_total_with_tax().toFixed(2),
#                         "status": 1,
#                         "insAmt": totalInsAmt,
#                         "vatAmt": order.amount_tax, #totalVat.toFixed(2),
#                         "netAmt": order.amount_total,
#                         "receiptNumber": order.receipt_number,
#                         "detCnt": detCnt, 
#                         "receiptId": order.receipt_id,
#                         "ebarimtDetails": emdStocks,
#                         "lastName": order.last_name,
#                         "firstName": order.first_name,
#                         "register": order.register,
#                         "origin": order.id,
#                     }
#                 _logger.info(u'Жорын мэдээлэл : %s', jsonData)
#                 config = self.env['pos.config'].browse(order.session_id.config_id.id)
#                 head = {'Authorization': 'Basic VV9mZl05Qmp5WlhMbUcmZHcmOlo3JHtFenlyRDRheUN9RkxkJg=='}
#                 data = {
#                     'grant_type': 'password',
#                     'username': config.user_name,
#                     'password': config.password,
#                 }
#                 emd_url = config.emd_url + '/oauth/token?'
#                 response = requests.post(emd_url, params=data, headers=head, verify=False)
                
#                 if response.status_code == 200:
#                     new_data = json.loads(response.text)
#                     access_token = new_data['access_token']
#                     recipt_send = self.send_emd(jsonData, config.id, access_token)
#         return ebarimt_data
        
    
#     def generate_order_json(self):
#         data = super(PosOrder, self).generate_order_json()
#         if self.receipt_number != False:
#             data['billIdSuffix'] = self.receipt_number
#         return data
    
#     @api.model
#     def send_emd(self, json_arg, pos_id, access_token):
#         '''
#         ЭМД -ын цахим системээс токен авч жорын дугаараар шалгах функц
#         '''
#         new_data = []
#         insurance_id = False
#         config_id = pos_id
#         conf_obj = self.env['pos.config']
#         insurance_obj = self.env['pos.insurance.sale']
#         insuranceLine_obj = self.env['pos.insurance.sale.line']
#         invoice_obj = self.env['account.move']
#         invoice_line_obj = self.env['account.move.line']
#         product_obj = self.env['product.product']
#         config = conf_obj.browse(config_id)
#         head = {"Content-Type": "application/json"}
#         myUrl = 'https://ws.emd.gov.mn/ebarimt/send?access_token=' + access_token
# #        myUrl = 'https://ws.emd.gov.mn/ebarimt/batch?access_token=' + access_token
#         datas_line = []
#         dt = datetime.strptime(json_arg['salesDate'], '%Y-%m-%d %H:%M:%S')
#         dt = dt.date()
#         unix_time = int(mktime(dt.timetuple())) * 1000
#         _logger.info(u'sales_date мэдээлэл : %s', unix_time)
#         for details in json_arg['ebarimtDetails']:
#             datas_line.append({
#                 "barCode": details['barCode'],
#                 "productName": details['productName'],
#                 "quantity": details['quantity'],
#                 "insAmt": details['insAmt'],
#                 "totalAmt": details['totalAmt'],
#                 "price": details['price'],
#                 "detailId": details['detailId'],
#                 "tbltId":details['tbltId'],
#                 "packGroup": details['packGroup']
#             })
#         datas  = {
#                 "receiptId": int(json_arg['receiptId']),
#                 "posRno": json_arg['posRno'],
#                 "salesDate": unix_time,
#                 "totalAmt": json_arg['totalAmt'],    # order.get_total_with_tax().toFixed(2),
#                 "status": 1,
#                 "insAmt": json_arg['insAmt'],
#                 "vatAmt": json_arg['vatAmt'], #totalVat.toFixed(2),
#                 "netAmt": json_arg['netAmt'],
#                 "receiptNumber": int(json_arg['receiptNumber']),
#                 "detCnt": json_arg['detCnt'],
#                 "ebarimtDetails": datas_line,
#             } 
#         # try:
#         emd_datas = json.dumps(datas)
#         _logger.info(u'emd_datas мэдээлэл : %s', emd_datas)
#         _logger.info(u'emd_datas type : %s', type(emd_datas))
#         _logger.info(u'URL мэдээлэл : %s', myUrl)
#         _logger.info(u'head мэдээлэл : %s', head)

#         response1 = requests.post(myUrl, headers=head, data=emd_datas, verify=False)
#         _logger.info(u'response1 мэдээлэл : %s', response1)
        # if response1.text:
        #     new_data = json.loads(response1.text)
        #     if new_data['code'] != '200':
        #         _logger.error(u'ЭМД системтэй холбогдож чадсангүй!. %s', new_data)
        #         raise ValidationError(u'ЭМД системтэй холбогдож чадсангүй!')

#         vals = {
#             'name': json_arg['receiptNumber'],
#             'date': json_arg['salesDate'],
#             'totalAmt': json_arg['totalAmt'],
#             'insAmt': json_arg['insAmt'],
#             'lastName': json_arg['lastName'],
#             'firstName': json_arg['firstName'],
#             'register': json_arg['register'],
#             'partner_id': config.emd_partner_id.id,
#             'origin': json_arg['origin'],
#             'state': 'sented',
#             'netAmt': json_arg['netAmt'],
#             'vatAmt': json_arg['vatAmt'],
#             'ddtd': json_arg['posRno'],
#             'receipt_id': json_arg['receiptId'],
#             'config_id': config.id,
#             "detCnt": json_arg['detCnt'],
#         }
#         insurance_id = insurance_obj.create(vals)
#         self._cr.execute("select id from account_move where partner_id = %s \
#                     and invoice_date = '%s' and journal_id = %s and state = 'draft'"
#                          % (config.emd_partner_id.id, json_arg['salesDate'], config.invoice_journal_id.id))
#         fetch_inv_id = self._cr.fetchone()
#         if fetch_inv_id == [] or not fetch_inv_id:
#             inv_id = invoice_obj.create(
#                 {
#                     'journal_id': config.invoice_journal_id.id,
#                     'invoice_date': json_arg['salesDate'],
#                     'company_id': config.company_id.id,
#                     'move_type': 'out_invoice',
#                     'state': 'draft',
#                     'partner_id': config.emd_partner_id.id,
#                 })
#         else:
#             inv_id = invoice_obj.search([('id', '=', fetch_inv_id[0])])
#         if insurance_id:
#             for details in json_arg['ebarimtDetails']:
#                 lvals = {
#                     'parent_id': insurance_id.id,
#                     'detail_id': details['detailId'],
#                     'product_id': details['product_id'],
#                     'quantity': details['quantity'],
#                     'insAmt': details['insAmt'],
#                     'price': details['price'],
#                     'totalAmt': details['totalAmt'],
#                 }
                
#                 insurance_line = insuranceLine_obj.create(lvals)
#                 if inv_id:
#                     product = product_obj.search([('id', '=', details['product_id'])])
#                     price_unit = float(details['insAmt']) / float(details['quantity'])
#                     account_id = product.categ_id.property_account_income_categ_id.id,
#                     invoice_line = {
#                             'product_id': product.id,
#                             'quantity': float(details['quantity']/product.package_qty),
#                             'price_unit': float(details['insAmt']) / float(details['quantity']/product.package_qty),
#                             'name': details['productName'],
#                             'product_uom_id': product.uom_id.id,
# #                             'move_id': inv_id.id,
#                             'tax_ids': [(6, 0, product.taxes_id.ids)],
#                             'account_id': account_id,
#                         }
#                     inv_id.write({'invoice_line_ids': [(0, None, invoice_line)]})
        # return new_data
