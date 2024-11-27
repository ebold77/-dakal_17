import collections
import requests, json
import logging

from odoo import models, fields, _
from odoo.tools import populate
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    is_contract = fields.Selection([('no_contract', 'No Contract'),
                               ('contract', 'Contract'),
                               ('loan_contract', 'Loan Contract')], string='Is Contract', default='no_contract')
    name = fields.Char(index=True, default = '*')
    partner_employee_name = fields.Char(string='Employee name')
    is_vatpayer = fields.Boolean(string ="Is Vatpaye", default=False)    

    
    def action_get_info(self):
        resp = requests.get("http://info.ebarimt.mn/rest/merchant/info?regno=" + self.vat)
   
        resp_json = json.loads(resp.text)
        
        if resp_json['name']:
            self.name = resp_json['name']
            print('resp_json vatpayer==========', resp_json['vatpayer'])
            if resp_json['vatpayer'] == True:
                self.is_vatpayer = True
        else:
            raise ValidationError(_(
                    "The customer with the registration number %s is not registered. \
                    \n Please check the company of registration number.", self.vat
                ))