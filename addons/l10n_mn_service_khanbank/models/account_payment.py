# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, fields, models, _
from odoo.tools.misc import remove_accents
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_repr
from .constants import *

import base64
import re


class AccountPayment(models.Model):
    _inherit = "account.payment"

    show_khanbank_data = fields.Boolean(compute='_compute_show_khanbank_data',
                                        help="Technical field used to know whether the khanbank related data to be displayed or not in the payments form views")
    direct_khanbank_pay = fields.Boolean(string="Direct khanbank pay", default=False)
    transaction_currency_type = fields.Selection(
        [('F', 'By sender\'s currency'), ('T', 'By beneficiary\'s account currency')],
        string="Transaction Currency Type", default='F')
    journal_currency_id = fields.Many2one('res.currency', related='journal_id.currency_id')
    account_balance = fields.Monetary(string='Account Balance', currency_field='journal_currency_id',
                                      compute='_compute_account_balance')
    transaction_type = fields.Selection(
        [('local', 'In local bank'), ('inter', 'Between different banks')],
        compute='_compute_transaction_type', default='local', string="Transaction Type")

    loginName = fields.Char('Login name', help='Login name given from Internet Bank in Khanbank')
    tranPassword = fields.Char('Password', help='Password given from Vasco in Khanbank')

    @api.depends('payment_type', 'journal_id', 'partner_bank_id')
    def _compute_transaction_type(self):
        for payment in self:
            payment.transaction_type = 'local'
            if payment.journal_id.bank_id.bic and str(
                    payment.journal_id.bank_id.bic).upper() == KHANBANK_NAME_UPPER:
                if payment.payment_type == 'outbound':
                    if payment.journal_id.bank_id == payment.partner_bank_id.bank_id:
                        payment.transaction_type = 'local'
                    elif payment.partner_bank_id.acc_type == 'bank':
                        payment.transaction_type = 'inter'

    @api.depends('payment_type', 'journal_id')
    def _compute_show_khanbank_data(self):
        for payment in self:
            # if not payment.journal_id.bank_id:
            #     raise ValidationError(
            #         _("Please define Journal '%s' bank account") % payment.journal_id.name)

            payment.show_khanbank_data = (payment.journal_id.bank_id.bic and str(
                payment.journal_id.bank_id.bic).upper() == KHANBANK_NAME_UPPER) and \
                                         payment.payment_type != 'inbound'
            if not payment.show_khanbank_data:
                payment.direct_khanbank_pay = False
                payment.account_balance = False
                payment.transaction_currency_type = False

    @api.depends('journal_id', 'direct_khanbank_pay', 'payment_method_code')
    def _compute_account_balance(self):
        if (self.journal_id.bank_id.bic and str(self.journal_id.bank_id.bic).upper() == KHANBANK_NAME_UPPER and \
                self.payment_method_code == KHANBANK_NAME_LOWER):
            self.account_balance = self.journal_id.bank_account_id.getBankBalance()
        else:
            self.account_balance = False

    @api.depends('payment_type')
    def _compute_show_partner_bank(self):
        for payment in self:
            payment.show_partner_bank_account = payment.payment_type != 'inbound'

    @api.onchange('payment_method_id')
    def _onchange_payment_method_id(self):
        if self.payment_method_id.code == KHANBANK_NAME_UPPER:
            self.direct_khanbank_pay = False

    @api.model
    def _get_method_codes_using_bank_account(self):
        res = super(AccountPayment, self)._get_method_codes_using_bank_account()
        res += [KHANBANK_NAME_LOWER]
        return res

    @api.model
    def _get_method_codes_needing_bank_account(self):
        res = super(AccountPayment, self)._get_method_codes_needing_bank_account()
        res += [KHANBANK_NAME_LOWER]
        return res

    @api.model
    def split_node(self, string_node, max_size):
        # Split a string node according to its max_size in byte
        byte_node = string_node.encode()
        if len(byte_node) <= max_size:
            return string_node, ''
        while byte_node[max_size] >= 0x80 and byte_node[max_size] < 0xc0:
            max_size -= 1
        return byte_node[0:max_size].decode(), byte_node[max_size:].decode()

    @api.model
    def _sanitize_communication(self, communication):
        """ Returns a sanitized version of the communication given in parameter,
            so that:
                - it contains only latin characters
                - it does not contain any //
                - it does not start or end with /
                - it is maximum 140 characters long
            (these are the Khanbank compliance criteria)
        """
        communication = self.split_node(communication, 140)[0]
        while '//' in communication:
            communication = communication.replace('//', '/')
        if communication.startswith('/'):
            communication = communication[1:]
        if communication.endswith('/'):
            communication = communication[:-1]
        communication = re.sub('[^-A-Za-zА-Яа-я0-9/?:().,\'+ ]', '', remove_accents(communication))
        return communication

    def create_request_payment(self):
        bank_account = self.partner_bank_id
        currency = self.currency_id and self.currency_id.name or self.company_id.currency_id.name
        data = {
            "fromAccount": str(self.journal_id.bank_account_id.sanitized_acc_number),
            "toAccount": str(bank_account.acc_number),
            "amount": float_repr(float_round(self.amount, 2), 2),
            "description": str(self._sanitize_communication(self.ref)),
            "currency": str(currency),
            "loginName": str(self.loginName),
            "tranPassword": base64.b64encode(str(self.tranPassword).encode("utf-8")).decode("utf-8"),
            "transferid": ""
        }

        if self.transaction_type == 'inter':
            if not bank_account.bank_id.bic:
                raise ValidationError(
                    _("Please define Bank Identifier Code for bank account '%s'") % bank_account.acc_number)
            khanbank_bank = self.env['khanbank.bank'].search(
                [('bic', '=', str(bank_account.bank_id.bic).lower())], limit=1)
            if len(khanbank_bank) == 0:
                raise ValidationError(
                    _("Please define Bank Identifier Code for Khanbank Banks '%s'") % bank_account.bank_id.bic)
            data["toAccountName"] = str(bank_account.acc_holder_name or bank_account.partner_id.name)
            data["toCurrency"] = currency
            data["toBank"] = str(khanbank_bank.code)
            if self.transaction_currency_type == 'T':
                data["toCurrency"] = str(
                    (bank_account.currency_id and bank_account.currency_id.name or self.company_id.currency_id.name))
        return data

    def sendKhanbankPaymentRequest(self):
        for payment in self:
            if not payment.transaction_type:
                raise ValidationError(_("Transaction type should be determined before bank operation!"))
            endpoint = 'transfer/domestic' if payment.transaction_type == 'local' else 'transfer/interbank'
            headers = {"Content-type": "application/json"}
            resp_json = self.env['account.online.provider']._khanbank_fetch('POST', endpoint, headers, None, None,
                                                                            self.create_request_payment())

    def action_post(self):
        for rec in self:
            if rec.direct_khanbank_pay:
                self.sendKhanbankPaymentRequest()
        return super(AccountPayment, self).action_post()
