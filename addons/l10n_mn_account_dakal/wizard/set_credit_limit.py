import time
from datetime import date, datetime
import logging
from urllib.request import urlopen
import re
from datetime import datetime
import simplejson as json

from odoo import models, fields, _
from odoo.tools import populate
from odoo.exceptions import ValidationError

class SetCreditLimit(models.TransientModel):
	_name = 'partner.limit.settings'
	_description = "Partner limit settings"

	current_date = fields.Date(string='Current Day', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
	check_date = fields.Date(string='Check Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
	category_id = fields.Many2one('res.partner.category', string="Category") 

	def set_credit_limit(self):
		
		partner_ids = self.env['res.partner'].search([('category_id.id','=', self.category_id.id)])
		for partner in partner_ids:
			amount_due = 0
			invoices = self.env['account.move'].search([('partner_id', '=', partner.id),
						('move_type','=','out_invoice'),
						('invoice_date','<=', self.check_date),
						('payment_state','!=', 'paid'),
						('state','=', 'posted')])
			for invoice in invoices:
				amount_due += invoice.amount_residual
			if amount_due > 10000:
				partner.write({'credit_check': True,
								'credit_warning': 10,
								'credit_blocking':10})
			else:
				partner.write({'credit_check': False})
		
