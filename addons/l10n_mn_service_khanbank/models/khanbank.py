# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

import datetime
import json
import logging

import requests
from cryptography.fernet import Fernet, InvalidToken
from requests.auth import HTTPBasicAuth

from odoo import fields, models, _
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from .constants import *

_logger = logging.getLogger(__name__)


class KhanbankProviderAccount(models.Model):
    _inherit = ['account.online.provider']

    provider_type = fields.Selection(selection_add=[(KHANBANK_NAME_LOWER, KHANBANK_NAME_UPPER)])

    def _khanbank_fetch(self, method, endpoint, headers=None, params=None, auth=None, data=None):
        if headers is None:
            headers = {"Content-type": "application/x-www-form-urlencoded"}
        if endpoint != 'auth/token':
            headers['Authorization'] = "Bearer " + self.get_access_token()
        if params is None:
            params = {}
        if auth is None:
            auth = {}
        if data is None:
            data = {}
        company = self.env.user.company_id
        try:
            url = '{}/{}'.format(company.khanbank_base_url, endpoint)
            response = requests.request(method=method,
                                        url=url, headers=headers, params=params, auth=auth, data=json.dumps(data))
            if response.status_code == 200:
                return response.json()
            else:
                raise UserError(
                    _("Not successful json request. Code: %s Reason: %s Response: %s") % (
                        response.status_code, response.reason, response.json()))
        except requests.exceptions.Timeout as e:
            _logger.exception(e)
            raise UserError(_('Timeout: the server did not reply within 60s'))
        except requests.exceptions.ConnectionError as e:
            _logger.exception(e)
            raise UserError(_('Server not reachable, please try again later'))
        except ValueError as e:
            _logger.exception(e)
            raise UserError(_('Invalid error: %s') % e)

    def decrypt(self, token):
        if not token:
            raise UserError(_('Khanbank username or password is empty. Please enter username and password'))
        if not ENCTYPTION_KEY:
            raise ValidationError(_(
                "No '%s' entry found in models/constants file. "
                "Use a key similar to: %s") % ('ENCTYPTION_KEY', Fernet.generate_key())
                                  )
        key = ENCTYPTION_KEY.encode()
        f = Fernet(key)
        try:
            data = f.decrypt(bytes(token, 'utf-8')).decode()
        except InvalidToken:
            raise ValidationError(_(
                "Password has been encrypted with a different "
                "key. Unless you can recover the previous key, "
                "this password is unreadable."))
        return data

    def get_access_token(self):
        company = self.env.user.company_id
        params = {'grant_type': 'client_credentials'}
        auth = HTTPBasicAuth(self.decrypt(company.khanbank_username), self.decrypt(company.khanbank_password))
        token = self._khanbank_fetch("POST", 'auth/token', None, params, auth)
        return token['access_token']

    def _get_available_providers(self):
        ret = super(KhanbankProviderAccount, self)._get_available_providers()
        ret.append(KHANBANK_NAME_LOWER)
        return ret

    def _update_khanbank_accounts(self, method='add'):
        resp_json = self._khanbank_fetch('GET', 'accounts')
        res = {'added': self.env['account.online.journal']}
        for account in resp_json.get('accounts', {}):
            vals = {
                'balance': account.get('balance', 0)
            }
            account_number = account.get('number', '')
            account_search = self.env['account.online.journal'].search(
                [('account_online_provider_id', '=', self.id), ('online_identifier', '=', account_number)],
                limit=1)
            if len(account_search) == 0:
                # Since we just create account, set last sync to 15 days in the past to retrieve transaction from latest 15 days
                last_sync = self.last_refresh - datetime.timedelta(days=15)
                vals.update({
                    'name': account_number,
                    'online_identifier': account_number,
                    'account_online_provider_id': self.id,
                    'account_number': account_number,
                    'last_sync': last_sync,
                })
                acc = self.env['account.online.journal'].create(vals)
                res['added'] += acc
        self.write({'status': 'SUCCESS', 'action_required': False})
        res.update({'status': 'SUCCESS',
                    'message': '',
                    'method': method,
                    'number_added': len(res['added']),
                    'journal_id': self.env.context.get('journal_id', False)})
        return self.show_result(res)

    def manual_sync(self):
        if self.provider_type != KHANBANK_NAME_LOWER:
            return super(KhanbankProviderAccount, self).manual_sync()

        transactions = []
        for account in self.account_online_journal_ids:
            if account.journal_ids:
                tr = account.retrieve_transactions()
                transactions.append({'journal': account.journal_ids[0].name, 'count': tr})

        self.write({'status': 'SUCCESS', 'action_required': False, 'last_refresh': fields.Datetime.now()})
        result = {'status': 'SUCCESS', 'transactions': transactions, 'method': 'refresh',
                  'added': self.env['account.online.journal']}
        return self.show_result(result)

    def update_credentials(self):
        if self.provider_type != KHANBANK_NAME_LOWER:
            return super(KhanbankProviderAccount, self).update_credentials()

        self.ensure_one()
        return self._update_khanbank_accounts()


class KhanbankAccount(models.Model):
    _inherit = 'account.online.journal'

    def retrieve_transactions(self):
        if (self.account_online_provider_id.provider_type != KHANBANK_NAME_LOWER):
            return super(KhanbankAccount, self).retrieve_transactions()

        if not self.journal_ids:
            return 0

        fromDate = self.last_sync or fields.Date.today()
        resp_json = self.account_online_provider_id._khanbank_fetch('GET', 'statements/%s' % self.online_identifier,
                                                                    None, {'from': fromDate.strftime("%Y%m%d")})
        end_amount = resp_json.get('endBalance', 0)
        transactions = []
        for transaction in resp_json.get('transactions', {}):
            account_number = transaction.get('relatedAccount', '')
            ref = str(transaction.get('record', ''))
            journal = str(transaction.get('journal', ''))
            trans = {
                'online_identifier': journal + '-' + ref + '-' + str(account_number),
                'date': fields.Date.from_string(transaction.get('tranDate', '')),
                'payment_ref': transaction.get('description', ''),
                'ref': ref,
                'amount': float(transaction.get('amount', 0)),
                'account_number': account_number,
                'online_partner_bank_account': account_number,
            }

            if account_number:
                partner_bank = self.env['res.partner.bank'].search(
                    [('sanitized_acc_number', '=', sanitize_account_number(account_number))], limit=1)

                if partner_bank:
                    trans['partner_bank_id'] = partner_bank.id
                    trans['partner_id'] = partner_bank.partner_id.id

            if not trans.get('partner_id') and transaction.get('attributes', {}).get('counterpartName'):
                trans['online_partner_vendor_name'] = transaction['attributes']['counterpartName']
                trans['partner_id'] = self._find_partner(
                    [('online_partner_vendor_name', '=', transaction['attributes']['counterpartName'])])

            transactions.append(trans)

        return self.env['account.bank.statement'].online_sync_bank_statement(transactions, self.journal_ids[0],
                                                                             end_amount)
