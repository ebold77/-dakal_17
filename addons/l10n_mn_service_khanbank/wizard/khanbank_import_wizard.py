# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero
from ..models.constants import *


class KhanbankDataWizard(models.TransientModel):
    _name = 'khanbank.wizard'
    _description = 'Khanbank Wizard'

    def import_khanbank_data(self):
        for khanbank_data_wizard in self:
            khanbank_data_wizard.load_from_gateway()

    @api.model
    def load_from_gateway(self):
        khanbank_provider = self.env['account.online.provider']
        self.loadCurrencyRate(khanbank_provider._khanbank_fetch('GET', 'rates'),
                              self.env['khanbank.currency.rate'])
        self.loadBank(self.env['khanbank.bank'])

    def loadBank(self, containerObj):
        for bank in BANKS:
            item = containerObj.search(
                [('name', '=', bank.get('name')), ('bic', '=', bank.get('bic'))])
            if not item:
                containerObj.create({'name': bank.get('name'), 'bic': bank.get('bic')})

    def loadCurrencyRate(self, jsonResponse, containerObj):
        for element in jsonResponse:
            name = element['name']
            symbol = element['currency']
            currency = self.env['khanbank.currency'].search([('symbol', '=', symbol)])
            if not currency:
                currency = self.env['khanbank.currency'].create({'name': name, 'symbol': symbol})
            elif currency.name != name:
                currency.name = name
            mid_rate = float(element['midRate'])
            buy_rate = float(element['buyRate'])
            sell_rate = float(element['sellRate'])
            item = containerObj.search([('name', '=', fields.Date.today()), ('currency_id', '=', currency.id)])
            if not item:
                containerObj.create(
                    {'currency_id': currency.id, 'mid_rate': mid_rate, 'buy_rate': buy_rate,
                     'sell_rate': sell_rate})
            elif (float_compare(item.mid_rate, mid_rate, precision_digits=2) != 0 or
                  float_compare(item.buy_rate, buy_rate, precision_digits=2) != 0 or
                  float_compare(item.sell_rate, sell_rate, precision_digits=2) != 0):
                item.mid_rate = mid_rate
                item.buy_rate = buy_rate
                item.sell_rate = sell_rate
