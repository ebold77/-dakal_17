# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
from functools import partial
import requests
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from .constants import *
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    bill_id = fields.Char(string='Bill ID', help="EBarimt Bill Id.")
    bill_printed_date = fields.Datetime(string='Bill Printed Date')
    bill_type = fields.Selection([('B2C_INVOICE','Individual Invoice'),('B2C_RECEIPT','Individual'),('B2B_RECEIPT','Company'),('B2B_INVOICE','Invoice')], default='B2C_RECEIPT')
    bill_mac_address = fields.Char(string='Bill MAC Address')
    tax_type = fields.Char(string='Bill Tax Type', compute='_tax_type')
    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)
    company_reg = fields.Char( string='companyReg')
    customer_tin = fields.Char( string='Customer Tin')
    company_name = fields.Char( string='Company Name')

    def _prepare_refund_values(self, current_session):
        self.ensure_one()

        ebarimt_url = "http://" +self.session_id.config_id.ebarimt_service_host +':'+ self.session_id.config_id.ebarimt_service_port+"/rest/receipt"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        refund_data = {}
        refund_data['id'] = self.bill_id
        refund_data['date'] = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_json = json.dumps(refund_data)
        response = requests.delete(url=ebarimt_url, data=data_json, headers=headers)
        if response.text:
            
            try:
                data = json.loads(response.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            # data_json = json.dumps(data)
            if data['status'] == 'ERROR':
                raise ValidationError(data['message'])
        return {
            'name': self.name + _(' REFUND'),
            'session_id': current_session.id,
            'date_order': fields.Datetime.now(),
            'pos_reference': self.pos_reference,
            'lines': False,
            'amount_tax': -self.amount_tax,
            'amount_total': -self.amount_total,
            'amount_paid': 0,

        }


    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)

        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)
        price = round(line.price_unit * (1 - (line.discount or 0.0) / 100.0),2)
        cur = line.order_id.pricelist_id.currency_id
        taxes = taxes.compute_all(price, cur, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)['taxes']
        val = 0.0
        for c in taxes:
            val += c.get('amount', 0.0)
        return val

    @api.depends('lines.price_subtotal_incl', 'lines.discount')
    def _compute_taxes(self):
        for order in self:
            currency = order.pricelist_id.currency_id
            order.amount_tax_vat = currency.round(sum(self._amount_tax(line, order.fiscal_position_id, TAX_TYPE_VAT) for line in order.lines))
            order.amount_tax_city = currency.round(sum(self._amount_tax(line, order.fiscal_position_id, TAX_TYPE_CITY) for line in order.lines))
    
    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['bill_type'] = ui_order['bill_type']
        order_fields['company_reg'] = ui_order['company_reg']
        order_fields['customer_tin'] = ui_order['customer_tin']
        print('order_fields.customer_tin', order_fields['customer_tin'])
        return order_fields

    def _tax_type(self):
        self.tax_type = None
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code in [TAX_TYPE_VAT, TAX_TYPE_CITY] for t in self.lines.tax_ids):
            self.tax_type = 'VAT_ABLE'

        if all(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_FREE for t in self.lines.tax_ids):
            self.tax_type = 'VAT_FREE'

        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_ZERO for t in self.lines.tax_ids):
            self.tax_type = 'VAT_ZERO'

    @api.model
    def get_merchant_info(self, urlInput):
        """ Get metchant info from ebarimt REST api """
        resp = requests.get(url=urlInput)
        data = None
        if resp:
            try:
                data = json.loads(resp.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            data_json = json.dumps(data)
            return data_json


    @api.model
    def get_customer_tin(self, vat):
        """ Get metchant info from ebarimt REST api """
        urlInput = "https://api.ebarimt.mn/api/info/check/getTinInfo?regNo=" + vat
        resp1 = requests.get(url=urlInput)
        data = None
        if resp1:
            try:
                data = json.loads(resp1.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)
            
            return data


    @api.model
    def get_company_name(self,number):
        names = u'%s'%number
        datas=names.upper()
        name = ''
        url="http://info.ebarimt.mn/rest/merchant/info?regno="+datas
        try:
            r = requests.get(url)
            n=r.json()
            deletearg = n['name'].replace("\n","")
            name=deletearg
        except Exception:
            r=' '
            name='' 
        return name


        
    @api.model
    def get_ebarimt(self, server_ids):
        ebarimt_data = []
           
        order = self.env['pos.order'].browse(server_ids['id'])

        if order.to_invoice:
            return ebarimt_data
        else:
            result = order.send_ebarimt()
            if 'lottery' in result and 'qrData' in result :
                ebarimt_data.append({'bill_id': result['id'], 'lottery': result['lottery'], 'qr_data': result['qrData']})
            elif 'qrData' in result:
                ebarimt_data.append({'bill_id': result['id'], 'qr_data': result['qrData']})
            else:
                ebarimt_data.append({'bill_id': result['id']})

        return ebarimt_data

    def generate_order_json(self):
        data = {}
        data['reportMonth'] = None
        data['districtCode'] = self.session_id.config_id.aimag_district_id.code or self.env['ebarimt.aimag.district'].search([('name','ilike',self.env.user.company_id.state_id.name)]).code
        data['merchantTin'] = self.session_id.config_id.merchant_tin
        data['branchNo'] = (self.session_id.config_id.branch_no or str(1)).zfill(3)
        data['posNo'] = (self.session_id.config_id.pos_no or str(1)).zfill(4)
        data['billIdSuffix'] = self.env['ir.sequence'].next_by_code('ebarimt.billid.suffix')
        data['type'] = self.bill_type

        if self.bill_type == 'B2B_RECEIPT':
            data['customerNo'] = self.company_reg 
            data['customerTin'] = self.customer_tin

        data['totalAmount'] = round(self.amount_total, 2)
        data['totalVat'] = round(self.amount_tax_vat, 2)
        data['totalCityTax'] = round(self.amount_tax_city, 2)
        data['taxType'] = self.tax_type
        data['“inactiveId”'] = self.bill_id or ""
        data['invoiceId'] = self.account_move and self.account_move.bill_id or ""

        return data

    def generate_order_line_json(self, order_line):
        items = {}
        items['name'] = order_line.product_id.name
        items['barCode'] = order_line.product_id.barcode
        if not order_line.product_id.barcode or len(order_line.product_id.barcode) < 13 :
            items['barCodeType'] = 'UNDEFINED'
            items['barCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        else:
            items['barCodeType'] = 'GS1'
        items['classificationCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        items['taxProductCode'] = ''
        items['measureUnit'] = order_line.product_id.uom_id.name
        items['qty'] = order_line.qty
        items['unitPrice'] =order_line.price_unit
        items['totalVAT'] = order_line.amount_tax_vat
        items['totalCityTax'] = order_line.amount_tax_city
        items['totalAmount'] = order_line.price_subtotal_incl
        # items['data'] = ''
       
        return items


    def send_ebarimt(self):
        order_json = self.generate_order_json()
        order_lines = []
        receipt = {}
        receipts = []
        payment = {}
        payments = []
        bankAccountNo_url = "http://info.ebarimt.mn/rest/bankAccounts?tin=" + self.session_id.config_id.merchant_tin

        for line in self.lines:
            if line.product_id.code:
                order_lines.append(self.generate_order_line_json(line))
        
        ###################### Receipts list #################
        receipt['items'] = order_lines
        resp1 = requests.get(url=bankAccountNo_url)
        bankAccountNo = None
        
        if resp1:
            try:
                data = json.loads(resp1.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            data_json = json.dumps(data)
            bankAccountNo = data_json['data']
        receipt['totalAmount'] = round(self.amount_total, 2)
        receipt['totalVat'] = round(self.amount_tax_vat, 2)
        receipt['totalCityTax'] = round(self.amount_tax_city, 2)
        receipt['taxType'] = self.tax_type
        receipt['bankAccountNo'] = bankAccountNo
        receipt['merchantTin'] = self.session_id.config_id.merchant_tin
        receipts.append(receipt)
        order_json['receipts'] = receipts

        ###################### Payments list #################
        
        for p in self.payment_ids:
        
            if p.payment_method_id.is_cash_count:
                payment['code'] = "CASH"
                payment['paidAmount'] = round(p.amount, 2)
                payment['status'] = "PAID"
            else:
                payment['code'] = "PAYMENT_CARD"
                payment['paidAmount'] = round(p.amount, 2)
                payment['status'] = "PAID"
            payments.append(payment)
        order_json['payments'] = payments

        ###################### GetInformation #################

        info_url = "http://" +self.session_id.config_id.ebarimt_service_host +':'+ self.session_id.config_id.ebarimt_service_port+"/rest/info"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.get(url=info_url, headers=headers)
        if response:
            try:
                res = json.loads(response.text)
                
            except Exception:
                error_message = traceback.format_exc()
                _logger.error(error_message)
        ###################### SendData #################
         
        ebarimt_url = "http://" + self.session_id.config_id.ebarimt_service_host +':'+ self.session_id.config_id.ebarimt_service_port+'/rest/receipt'
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.post(url=ebarimt_url, headers=headers, json=order_json)
        if response.text:
            
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
       

        return data

    def print_ebarimt(self):
        self.ensure_one()
        result = self.send_ebarimt()
        data = { 'model': 'pos.order',
                 # 'lottery_no': result['lottery'],
                 'qr_data': result['qrData'],
               }

        return self.env.ref('l10n_mn_ebarimt_3_0.action_report_ebarimt_pos_receipt').report_action(self, data=data)

    
    