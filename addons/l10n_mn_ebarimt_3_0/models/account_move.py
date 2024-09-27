# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import requests
import json
from .constants import *
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    bill_id = fields.Char(string='Bill ID', help="EBarimt Bill Id.")
    bill_printed_date = fields.Datetime(string='Bill Printed Date')
    bill_type = fields.Selection([('B2C_INVOICE','Individual Invoice'),('B2B_INVOICE','Invoice'),('B2C_RECEIPT','Individual'),('B2B_RECEIPT','Company')], default='B2B_RECEIPT')
    bill_mac_address = fields.Char(string='Bill MAC Address')
    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)
    tax_type = fields.Char(string='Bill Tax Type', compute="_tax_type")

    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.move_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)

        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)

        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        cur = line.move_id.currency_id
        taxes = taxes.compute_all(price, cur, line.quantity, product=line.product_id, partner=line.move_id.partner_id or False)['taxes']
        val = 0.0
        for c in taxes:
            val += c.get('amount', 0.0)
        return val

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.discount')
    def _compute_taxes(self):
        for move in self:
            currency = move.currency_id
            move.amount_tax_vat = currency.round(sum(self._amount_tax(line, move.fiscal_position_id, TAX_TYPE_VAT) for line in move.invoice_line_ids))
            move.amount_tax_city = currency.round(sum(self._amount_tax(line, move.fiscal_position_id, TAX_TYPE_CITY) for line in move.invoice_line_ids))

    def _tax_type(self):
        self.tax_type = None
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code in [TAX_TYPE_VAT, TAX_TYPE_CITY] for t in self.invoice_line_ids.tax_ids):
            self.tax_type = 'VAT_ABLE'

        if all(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_FREE for t in self.invoice_line_ids.tax_ids):
            self.tax_type = 'VAT_FREE'

        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_ZERO for t in self.invoice_line_ids.tax_ids):
            self.tax_type = 'VAT_ZERO'
  
    def print_ebarimt(self):
        self.ensure_one()
        result = self.send_ebarimt()       
        if 'lottery' in result :
                data = { 'model': 'account.move',
                         'lottery_no': result['lottery'],
                         'qr_data': result['qrData'],
                       }
        else:
            data = { 'model': 'account.move',
                     'qr_data': result['qrData'],
                   }
        return self.env.ref('l10n_mn_ebarimt_3_0.action_report_ebarimt_invoice').report_action(self, data=data)


    def generate_invoice_json(self, bill_type):
       
        data = {}
        data['reportMonth'] = None
        data['districtCode'] = self.company_id.aimag_district_id.code or self.env['ebarimt.aimag.district'].search([('name','ilike',self.env.user.company_id.state_id.name)]).code
        data['merchantTin'] = self.company_id.merchant_tin
        data['branchNo'] = '0001'
        data['posNo'] = '0001' #(self.session_id.config_id.pos_no or str(1)).zfill(4)
        data['billIdSuffix'] = self.env['ir.sequence'].next_by_code('ebarimt.billid.suffix')
        data['type'] = bill_type
        if self.bill_type == 'B2B_INVOICE' or self.bill_type == 'B2B_RECEIPT' :
            data['customerNo'] = self.partner_id.vat     
            
            data['customerTin'] = self.partner_id.get_customer_tin(self.partner_id.vat)

        data['totalAmount'] = self.amount_total
        data['totalVat'] = round(self.amount_total - self.amount_total/1.1, 2)
        data['totalCityTax'] = self.amount_tax_city
        data['taxType'] = self.tax_type
        data['“inactiveId”'] = self.bill_id or ""
        data['invoiceId'] = self.bill_id or ""

        print('oder json data------------>>', data)
        return data


    def generate_invoice_line_json(self, order_line):
        
        items = {}
        items['name'] = order_line.product_id.name
        items['barCode'] = order_line.product_id.barcode
        if not order_line.product_id.barcode or len(order_line.product_id.barcode) < 13:
            items['barCodeType'] = 'UNDEFINED'
            items['barCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        else:
            items['barCodeType'] = 'GS1'
        items['classificationCode'] = order_line.product_id.ebarimt_gs1barcode_id.code
        items['taxProductCode'] = ''
        items['measureUnit'] = order_line.product_id.uom_id.name
        items['qty'] = order_line.quantity
        items['unitPrice'] =order_line.price_unit
        items['totalVAT'] = order_line.amount_tax_vat
        items['totalCityTax'] = order_line.amount_tax_city
        items['totalAmount'] = (order_line.price_unit * (1 - order_line.discount/100))* order_line.quantity 

       
        return items


    def send_ebarimt(self):
        order_json = self.generate_invoice_json(self.bill_type)
        order_lines = []
        receipt = {}
        receipts = []
        payment = {}
        payments = []
        bankAccountNo_url = "http://info.ebarimt.mn/rest/bankAccounts?tin=" + self.company_id.merchant_tin

        for line in self.invoice_line_ids:
            if line.product_id.code:
                order_lines.append(self.generate_invoice_line_json(line))
        print('order_lines', order_lines)
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
            print('data_json', data_json)
            bankAccountNo = data_json['data']
        print('self.amount_tax_vat===', self.amount_tax_vat)
        receipt['totalAmount'] = self.amount_total
        receipt['totalVat'] = round(self.amount_total - self.amount_total/1.1, 2)
        receipt['totalCityTax'] = self.amount_tax_city
        receipt['taxType'] = self.tax_type
        receipt['bankAccountNo'] = bankAccountNo
        receipt['merchantTin'] = self.company_id.merchant_tin
        receipts.append(receipt)
        order_json['receipts'] = receipts

        ###################### Payments list #################
        if self.bill_type == 'B2B_RECEIPT' or self.bill_type == 'B2C_RECEIPT' :
            payment['code'] = "PAYMENT_CARD"
            payment['paidAmount'] = self.amount_total
            payment['status'] = "PAID"
            payments.append(payment)
        order_json['payments'] = payments

        exchange_data = {
        }
        order_json['exchangeData'] = exchange_data
        
        data = {}
        ebarimt_url = "http://" + self.company_id.ebarimt_service_host +':'+ self.company_id.ebarimt_service_port+'/rest/receipt'
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.post(url=ebarimt_url, headers=headers, json=order_json)
        print('response==============>>>', response.text)
        if response.text:
            try:
                data = json.loads(response.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)
            
        if data['status'] == 'ERROR':
            raise ValidationError(data['message'])

        if 'id' in data:
            self.bill_id = data['id']
            self.bill_printed_date = fields.Datetime.from_string(data['date'])
           

        return data
    