import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from odoo import fields
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestKhanbankTransfer(AccountTestInvoicingCommon):

    def create_account_provider(self):
        return self.env['account.online.provider'].create({
            'name': 'test',
            'provider_type': 'khanbank',
            'provider_account_identifier': '123',
            'provider_identifier': 'khanbank',
            'status': 'SUCCESS',
            'status_code': 0,
            'account_online_journal_ids': [
                (0, 0, {
                    'name': 'myAccount',
                    'account_number': '0000',
                    'online_identifier': '123123',
                    'balance': 500.0,
                    'last_sync': datetime.today() - relativedelta(days=15),
                }),
            ],
        })

    def test_khanbank_fetch_transactions(self):
        acc_online_provider = self.create_account_provider()
        self.bank_journal.account_online_journal_id = acc_online_provider.account_online_journal_ids

        informations = json.dumps(
            [{"providerAccountId": 123, "bankName": "Khanbank", "status": "SUCCESS", "providerId": 16441}])
        ret = self.env['account.online.provider'].callback_institution(informations, 'add', self.bank_journal.id)
        bank_stmt_all = self.env['account.bank.statement'].search([('journal_id', '=', self.bank_journal.id)])
        bank_stmt = bank_stmt_all[0]
        self.assertEqual(len(bank_stmt), 1)
        self.assertEqual(len(bank_stmt.line_ids), self.statement_count)
        self.assertEqual(bank_stmt.state, 'open')
        self.assertEqual(bank_stmt.line_ids.amount, -12345.12)
        self.assertEqual(bank_stmt.line_ids.online_identifier, "2829798:bank")
        self.assertEqual(bank_stmt.line_ids.partner_id, self.env['res.partner'])  # No partner defined on line
        self.assertEqual(acc_online_provider.account_online_journal_ids.last_sync, fields.Date.today())

        # Call again and check that we don't have any new transactions
        acc_online_provider.account_online_journal_ids.last_sync = fields.Date.today() - relativedelta(days=15)
        acc_online_provider.callback_institution(informations, 'add', self.bank_journal.id)
        bank_stmt = self.env['account.bank.statement'].search([('journal_id', '=', self.bank_journal.id)])
        self.assertEqual(len(bank_stmt), len(bank_stmt_all))
        self.assertEqual(len(bank_stmt[0].line_ids), self.statement_count)

    def test_khanbank_create_institution(self):
        informations = json.dumps(
            [{"providerAccountId": 123, "bankName": "Khanbank", "status": "SUCCESS", "providerId": 16441}])
        res = self.env['account.online.provider'].callback_institution(informations, 'add', self.bank_journal.id)
        acc_online_provider = self.env['account.online.provider'].search(
            [('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(acc_online_provider), 1)
        self.assertEqual(acc_online_provider.name, 'Khanbank')
        self.assertEqual(acc_online_provider.provider_type, 'khanbank')
        self.assertEqual(acc_online_provider.provider_account_identifier, '123')
        self.assertEqual(acc_online_provider.provider_identifier, '16441')
        self.assertEqual(acc_online_provider.status, 'SUCCESS')
        self.assertEqual(len(acc_online_provider.account_online_journal_ids))
        self.assertEqual(acc_online_provider.account_online_journal_ids.name, 'SMB account')
        self.assertEqual(acc_online_provider.account_online_journal_ids.account_number, 'xxxx4933')
        self.assertEqual(acc_online_provider.account_online_journal_ids.online_identifier, '123123')
        self.assertEqual(acc_online_provider.account_online_journal_ids.balance, 84699)
        self.env['account.online.provider'].callback_institution(informations, 'add', self.bank_journal.id)
        acc_online_provider = self.env['account.online.provider'].search(
            [('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(acc_online_provider), 1)
        self.assertEqual(len(acc_online_provider.account_online_journal_ids), 1)

    def test_khanbank_create_institution_fail(self):
        self.no_account = True
        informations = json.dumps([{"providerAccountId": 123, "bankName": "Khanbank", "status": "FAILED",
                                    "reason": "crashMsg", "providerId": 16441}])
        res = self.env['account.online.provider'].callback_institution(informations, 'add', self.bank_journal.id)
        acc_online_provider = self.env['account.online.provider'].search(
            [('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(acc_online_provider), 1)
        self.assertEqual(acc_online_provider.name, 'Khanbank')
        self.assertEqual(acc_online_provider.provider_type, 'khanbank')
        self.assertEqual(acc_online_provider.provider_account_identifier, '123')
        self.assertEqual(acc_online_provider.provider_identifier, '16441')
        self.assertEqual(acc_online_provider.status, 'FAILED')

    def test_khanbank_create_institution_between(self):
        self.no_account = True
        informations = json.dumps(
            [{"providerAccountId": 123, "bankName": "Khanbank", "status": "ACTION_ABANDONED", "providerId": 16441}])
        res = self.env['account.online.provider'].callback_institution(informations, 'add', self.bank_journal.id)

        acc_online_provider = self.env['account.online.provider'].search(
            [('company_id', '=', self.company_data['company'].id)])
        self.assertEqual(len(acc_online_provider), 1)
        self.assertEqual(acc_online_provider.name, 'Khanbank')
        self.assertEqual(acc_online_provider.provider_type, 'khanbank')
        self.assertEqual(acc_online_provider.provider_account_identifier, '123')
        self.assertEqual(acc_online_provider.provider_identifier, '16441')
        self.assertEqual(acc_online_provider.status, 'ACTION_ABANDONED')
