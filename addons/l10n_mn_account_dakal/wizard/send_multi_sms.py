import logging
from urllib.request import urlopen
import re
from datetime import datetime
import simplejson as json

from odoo import models, fields, _
from odoo.tools import populate
from odoo.exceptions import ValidationError

class SendMultiSms(models.TransientModel):
	_name = 'send.multi.sms'
	_description = "Web 2 multi sms"


	partner_ids = fields.Many2many('res.partner', 'send_multi_sms_partner_rel', 'wizard_id', 'partner_id', 'Partner')
	invoice_ids = fields.Many2many('account.move', 'send_multi_sms_invoice_rel', 'wizard_id', 'mvoe_id', 'Partner', 
		domain="[('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),('payment_state','!=', 'paid')]")
	sms_type = fields.Selection([('rent', 'Rent'),
                               ('sale', 'Sale')], string='SMS type', required=True)

	def send_sms(self):

		if self.partner_ids:
			partner_ids =  self.partner_ids
		# elif self.sms_type == 'rent':
		# 	partner_ids = self.env['res.partner'].search([('category_id.id','=', 74)])
		# else:
		# 	partner_ids = self.env['res.partner'].search([('category_id.id','!=', 74)])
		
			for partner in partner_ids:
				partner.send_sms_partner(sms_type=self.sms_type)

		if self.invoice_ids:

			for invoice in self.invoice_ids:
				invoice.send_sms(sms_type=self.sms_type)


