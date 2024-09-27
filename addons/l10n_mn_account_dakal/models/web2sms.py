# -*- coding: utf-8 -*-
##############################################################################
#
#    Dakal Pharma LLC, Enterprise Management Solution
#    Copyright (C) 2001-2019 Dakal Pharma LLC (<http://www.dklgr.mn/;). All Rights Reserved
#
#    Email : info@dakal.mn
#    Phone : 976 + 95762987, 976 + 99065724
#
##############################################################################

import logging
from collections import defaultdict
from datetime import datetime, time
from dateutil import relativedelta
from itertools import groupby
from json import dumps
from psycopg2 import OperationalError

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import add, float_compare, frozendict, split_every, format_date

_logger = logging.getLogger(__name__)

class web2sms(models.Model):
    _name = "web.to.sms"
    _description = "Web 2 sms"
    _inherit = ['mail.thread']
    _order = 'date DESC'

    
    state = fields.Selection([('draft', 'Draft'),
                               ('success', 'Success')], string='Status', default='draft')
    name = fields.Selection([('rent', 'Rent'),
                               ('sale', 'Sale')], string='Sms type')
    invoice_id = fields.Many2one('account.move', 'Account Move')
    date = fields.Datetime('Send date')
    partner_id = fields.Many2one('res.partner', 'Partner name')
    sms_number = fields.Char('Sent number')
    user_id = fields.Many2one('res.users','Sent user')
    sms_value = fields.Char('Value')
 

class web2sms_token(models.Model):
    _name = "webto.sms.token"
    _description = "Web 2 sms token"
    _inherit = ['mail.thread']

    
    token = fields.Char('Token')


class web2sms_value(models.Model):
    _name = "webto.sms.value"
    _description = "Web 2 sms value"
    _inherit = ['mail.thread']

    
    name = fields.Selection([('rent', 'Rent'),
                               ('sale', 'Sale')], string='SMS type', Translate=True)
    key1 = fields.Char('Key1')
    const1 = fields.Char('constant1', readonly=True, default = 'Харилцагчийн нэр')
    key2 = fields.Char('Key2')
    const2 = fields.Char('constant2', readonly=True, default = 'Огноо')
    key3 = fields.Char('Key3')
    const3 = fields.Char('constant3', readonly=True, default = 'Мөнгөн дүн')
    key4 = fields.Char('Key4')
   
    