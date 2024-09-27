# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import requests
import json
import logging
from datetime import date, datetime
from odoo.exceptions import UserError
from .constants import *
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    bill_id = fields.Char(string='Bill ID', help="EBarimt Bill Id.")
    bill_printed_date = fields.Datetime(string='Bill Printed Date')
    bill_mac_address = fields.Char(string='Bill MAC Address')
    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)
    bill_type = fields.Selection([('B2C_RECEIPT','Individual'),('B2B_RECEIPT','Company')], default='B2C_RECEIPT')

    @api.depends('amount_tax_vat','amount_tax_city')
    def _compute_taxes(self):
        for payment in self:
            currency = payment.currency_id
            payment.amount_tax_vat = currency.round(sum(invoice.amount_tax_vat for invoice in payment.reconciled_invoice_ids))
            payment.amount_tax_city = currency.round(sum(invoice.amount_tax_city for invoice in payment.reconciled_invoice_ids))

    def generate_payment_json(self):
        data = {}
        data['group'] = True
        data['vat'] = "%.2f" % self.amount_tax_vat
        data['amount'] = "%.2f" % self.amount
        data['billIdSuffix'] = ""
        data['posNo'] = str(1).zfill(6)

        return data


    def send_ebarimt(self):

        receipt = {}
        receipts = []
        payment = {}
        payments = []
        bankAccountNo_url = "http://info.ebarimt.mn/rest/bankAccounts?tin=" + self.company_id.merchant_tin
        if self.reconciled_invoice_ids:
            if len(self.reconciled_invoice_ids) > 1:
                # payment_json = self.generate_payment_json()

                bill_lines = []
                index = 0
                for invoice in self.reconciled_invoice_ids:
                    
                    bill_lines.append(invoice.generate_invoice_json(self.bill_type))

                    invoice_lines = []
                    for line in invoice.invoice_line_ids:
                        if line.product_id.code:
                            invoice_lines.append(invoice.generate_invoice_line_json(line))

                    payment_json['bills'] = bill_lines
                    payment_json['bills'][index]['stocks'] = invoice_lines
                    index += 1
            elif len(self.reconciled_invoice_ids) == 1:
                invoice = self.reconciled_invoice_ids
                if invoice.bill_type == 'B2B_RECEIPT' or invoice.bill_type == 'B2C_RECEIPT':
                    raise UserError(u'Энэ төлбөрийн нэхэмжлэлийг шууд борлуулалтаар бүртгэсэн тул дахин баримт бүртгэхгүй.')

                payment_json = invoice.generate_invoice_json(self.bill_type)
                print('payment_json+++++++>>', payment_json)
                payment_json['invoiceId'] = invoice.bill_id
                invoice_lines = []
                for line in invoice.invoice_line_ids:
                    invoice_lines.append(invoice.generate_invoice_line_json(line))
                    print('invoice_lines', invoice_lines)
                ###################### Receipts list #################
                receipt['items'] = invoice_lines
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
                receipt['totalAmount'] = payment_json['totalAmount']
                receipt['totalVat'] = payment_json['totalVat']
                receipt['totalCityTax'] =payment_json['totalCityTax']
                receipt['taxType'] = payment_json['taxType']
                receipt['bankAccountNo'] = bankAccountNo
                receipt['merchantTin'] = self.company_id.merchant_tin
                receipts.append(receipt)
                payment_json['receipts'] = receipts

                ###################### Payments list #################
                if self.bill_type == 'B2B_RECEIPT' or self.bill_type == 'B2C_RECEIPT' :
                    payment['code'] = "PAYMENT_CARD"
                    payment['paidAmount'] = self.amount_total
                    payment['status'] = "PAID"
                    payments.append(payment)
                payment_json['payments'] = payments

                data = {}

                print('payment_json=============>>>', payment_json)

                ebarimt_url = "http://" + self.company_id.ebarimt_service_host +':'+ self.company_id.ebarimt_service_port+'/rest/receipt'
                headers = {"Content-Type": "application/json; charset=utf-8"}
                response = requests.post(url=ebarimt_url, headers=headers, json=payment_json)
                
                if response:
                    try:
                        data = json.loads(response.text)
                    except Exception as e:
                        raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

                    # data_json = json.dumps(data)
                    print('data_json', data)
                
                if 'id' in data:
                    self.bill_id = data['id']
                    self.bill_printed_date = fields.Datetime.from_string(data['date'])
                    return data
        return False

    def print_ebarimt(self):
        self.ensure_one()
        result = self.send_ebarimt()
        data = None
        if result:
            if 'lottery' in result:
                data = { 'model': 'account.payment',
                         'lottery_no': result['lottery'],
                         'qr_data': result['qrData'],
                       }
            else:
                data = { 'model': 'account.payment',
                         'qr_data': result['qrData'],
                       }
        print('data=========', data)
        return self.env.ref('l10n_mn_ebarimt_3_0.action_report_ebarimt_payment').report_action(self, data=data)

    def generate_return_bill_json(self, account_payment):
        data = {}
        data['returnBillId'] = account_payment.bill_id
        data['date'] = account_payment.bill_printed_date.strftime('%Y-%m-%d %H:%M:%S')
        return data

    # def cancel(self):
    #     res = super(AccountPayment, self).cancel()
    #     for rec in self:
    #         if rec.bill_id:
    #             self.env['ebarimt.service'].returnBill(data=json.dumps(self.generate_return_bill_json(rec),indent=2), library_filename=rec.company_id.pos_library_filename)
    #             rec.bill_id = False
