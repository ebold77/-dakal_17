# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, fields, models

class KhanbankCurrency(models.Model):
    _name = 'khanbank.currency'
    _description = 'Khanbank Currency'

    # Note: 'code' column was removed as of v6.0, the 'name' should now hold the ISO code.
    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Code', required=True)
    mid_rate = fields.Float(compute='_compute_current_mid_rate', string='Mid Rate', digits=0,
                            help='The rate of the currency to the currency of rate 1.')
    buy_rate = fields.Float(compute='_compute_current_buy_rate', string='Buy Rate', digits=0,
                            help='The rate of the currency to the currency of rate 1.')
    sell_rate = fields.Float(compute='_compute_current_sell_rate', string='Sell Rate', digits=0,
                             help='The rate of the currency to the currency of rate 1.')
    rate_ids = fields.One2many('khanbank.currency.rate', 'currency_id', string='Rates')
    date = fields.Date(compute='_compute_date')

    @api.depends('rate_ids.mid_rate')
    def _compute_current_mid_rate(self):
        for currency in self:
            currency.mid_rate = currency.rate_ids[:1].mid_rate or 1.0

    @api.depends('rate_ids.buy_rate')
    def _compute_current_buy_rate(self):
        for currency in self:
            currency.buy_rate = currency.rate_ids[:1].buy_rate or 1.0

    @api.depends('rate_ids.sell_rate')
    def _compute_current_sell_rate(self):
        for currency in self:
            currency.sell_rate = currency.rate_ids[:1].sell_rate or 1.0

    @api.depends('rate_ids.name')
    def _compute_date(self):
        for currency in self:
            currency.date = currency.rate_ids[:1].name


class KhanbankCurrencyRate(models.Model):
    _name = 'khanbank.currency.rate'
    _description = 'Khanbank Currency Rate'
    _order = "name desc"

    name = fields.Date(string='Date', required=True, index=True, default=lambda self: fields.Date.today())
    currency_id = fields.Many2one('khanbank.currency', string='Currency', required=True)
    mid_rate = fields.Float(string='Mid Rate', required=True, digits=(18, 5), default=1.0,
                            help='The rate of the currency to the currency of rate 1')
    buy_rate = fields.Float(string='Buy Rate', required=True, digits=(18, 5), default=1.0,
                            help='The rate of the currency to the currency of rate 1')
    sell_rate = fields.Float(string='Sell Rate', required=True, digits=(18, 5), default=1.0,
                             help='The rate of the currency to the currency of rate 1')

    _sql_constraints = [
        ('unique_name_per_day', 'unique (name,currency_id)', 'Only one currency rate per day allowed!'),
        ('currency_rate_check', 'CHECK (buy_rate>0 OR sell_rate>0 OR mid_rate>0)',
         'The currency rate must be strictly positive.'),
    ]


class KHANBANKBank(models.Model):
    _name = 'khanbank.bank'
    _description = 'KHANBANK Bank Parameters'

    name = fields.Char(string='Name', required=True)
    bic = fields.Char(string='Bank Identifier Code', required=True)