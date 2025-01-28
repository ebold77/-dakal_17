#-*- coding: utf-8 -*-
from odoo import api, models, fields
from datetime import datetime
from odoo.addons.l10n_mn_report.models.report_helper import verbose_numeric, comma_me, convert_curr


class ReportPartnerBillBalanceAct(models.AbstractModel):
    _name = 'report.l10n_mn_account_bill_balance_act.bill_balance_act'
    _description = 'Report Partner Bill Balance Act'

    @api.model
    def _get_report_values(self, docids, data=None):
        move_line_obj = self.env['account.move.line']
        partner = self.env['res.partner'].browse(data['partner_id'])
        company = self.env['res.company'].browse(data['company_id'])
        partner_bank_number = partner_bank_name = company_bank_number = company_bank_name = False
        if data['write_partner_respondent_bank_id']:
            partner_bank = self.env['res.partner.bank'].browse(data['write_partner_respondent_bank_id'])
            partner_bank_name = partner_bank.bank_id and partner_bank.bank_id.name or False
            partner_bank_number = partner_bank.acc_number
        if data['write_respondent_bank_id']:
            company_bank = self.env['res.partner.bank'].browse(data['write_respondent_bank_id'])
            company_bank_name = company_bank.bank_id and company_bank.bank_id.name or False
            company_bank_number = company_bank.acc_number

        lines = move_line_obj.with_context(partner_ids=partner.ids, order_by='p.name, aa.code, aa.name').get_all_balance(company, data['account_ids'],
                                                                                                                         data['date_start'], data['date_stop'], 'posted')
        total_start = total_currency_start = total_debit = total_currency_debit = 0
        total_credit = total_currency_credit = total_end = total_currency_end = 0
        verbose_total = ''
        if lines:
            account_type = data['account_type']
            for line in lines: 
                end = line['start_balance'] + line['debit'] - line['credit']
                currency_end = line['cur_start_balance'] + line['cur_debit'] - line['cur_credit']
                if end != 0 or currency_end != 0:
                    total_start += line['start_balance']
                    total_currency_start += line['cur_start_balance']
                    total_debit += line['debit']
                    total_currency_debit += line['cur_debit']
                    total_credit += line['credit']
                    total_currency_credit += line['cur_credit']
                    total_end += line['start_balance'] + line['debit'] - line['credit']
                    total_currency_end += line['cur_start_balance'] + line['cur_debit'] - line['cur_credit']
                    # Данснууд сонгоход 1 төрлийн данс сонгосон эсэхийг шалгахын тулд өмнөх дансны төрлийг хадгална
                    if account_type == 'choose_accounts':
                        atype = line['atype']
                word = verbose_numeric(abs(total_end))
                curr = self.env.company.currency_id.integer
                div_curr = self.env.company.currency_id.divisible
                symbol = self.env.company.currency_id.symbol
                verbose_total = convert_curr(word, curr, div_curr)
        date_start = data['date_start'] 
        date_stop = data['date_stop']
        partner_sign = (data['write_partner_respondent_surname'][0] + '. ' if data['write_partner_respondent_surname'] else '')\
                       + (data['write_partner_respondent_firstname'] if data['write_partner_respondent_firstname'] else '')
        company_sign = (data['write_respondent_surname'][0] + '. ' if data['write_respondent_surname'] else '') + \
                       (data['write_respondent_firstname'] if data['write_respondent_firstname'] else '')
        return {'docs': partner,
                'doc_ids': partner.ids,
                'doc_model': 'report.bill.balance.act',
                'company': company,
                'partner': partner,
                'first_residual': total_start,
                'total_residual': total_end,
                'verbose_total': verbose_total,
                'type': data['type'],
                'start_year': datetime.strptime(date_start, '%Y-%m-%d').year,
                'start_month': datetime.strptime(date_start, '%Y-%m-%d').month,
                'start_day': datetime.strptime(date_start, '%Y-%m-%d').day,
                'stop_year': datetime.strptime(date_stop, '%Y-%m-%d').year,
                'stop_month': datetime.strptime(date_stop, '%Y-%m-%d').month,
                'stop_day': datetime.strptime(date_stop, '%Y-%m-%d').day,
                'write_partner_respondent_job_title': data['write_partner_respondent_job_title'],
                'write_partner_respondent_surname': data['write_partner_respondent_surname'],
                'write_partner_respondent_firstname': data['write_partner_respondent_firstname'],
                'partner_bank_name': partner_bank_name,
                'partner_bank_number': partner_bank_number,
                'partner_sign': partner_sign,
                'write_respondent_job_title': data['write_respondent_job_title'],
                'write_respondent_surname': data['write_respondent_surname'],
                'write_respondent_firstname': data['write_respondent_firstname'],
                'company_bank_name': company_bank_name,
                'company_bank_number': company_bank_number,
                'company_sign': company_sign,
                }