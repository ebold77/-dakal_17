# -*- coding: utf-8 -*-
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def _download_currency_rate(self):
        rate_obj = self.env['res.currency.rate']
        for record in self:
            rate = requests.get('http://monxansh.appspot.com/xansh.json?currency=' + record.name)
            rate_json = rate.json()
            rate = rate_json[0]['rate_float']
            date = datetime.strptime(rate_json[0]['last_date'], DEFAULT_SERVER_DATETIME_FORMAT)
            if date.day != fields.Date.today().day:
                date = date + relativedelta(days=1)
            companies = self.env['res.company'].search([])
            if companies:
                for company in companies:
                    existing_rate = rate_obj.search([('currency_id', '=', record.id),
                                                     ('name', '=', date),
                                                     ('company_id', '=', company.id)])
                    if not existing_rate:
                        rate_obj.create({
                            'currency_id': record.id,
                            'name': date,
                            'rate': 1/rate,
                            'company_id':company.id
                        })
