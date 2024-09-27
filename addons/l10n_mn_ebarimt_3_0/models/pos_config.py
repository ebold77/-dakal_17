# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import api, fields, models
import requests, json

import traceback
# import requests
import urllib
import urllib.request as urllib2
from urllib.error import HTTPError

import logging
_logger = logging.getLogger(__name__)

class pos_config(models.Model):
    _inherit = 'pos.config'

    aimag_district_id = fields.Many2one('ebarimt.aimag.district', string="Aimag/District", help="This Aimag/District will be assigned by default on new EBarimt put operation.")
    # library_filename = fields.Char(string="Library Filename", required=True, default='libPosAPI.so', help="Specific setting of library file name for POS. Each POS can use different files.")
    branch_no = fields.Char(string="Branch No", required=True, default="001")
    pos_no = fields.Char(string="POS No", required=True, default="0001")
    ebarimt_service_host = fields.Char(string='Ebarimt service address', default= '49.0.129.29')
    ebarimt_service_port = fields.Char(string='Ebarimt service port', default= '7080')
    merchant_tin = fields.Char(string='Merchant Tin')

    @api.model
    def get_partner_info(self, vat):
        resp = requests.get("http://info.ebarimt.mn/rest/merchant/info?regno=" + vat)
        resp_json = json.loads(resp.text)

        data={}
        data['name'] = resp_json['name']
        return data

    @api.model
    def get_partner_tin(self, vat):
        partner_tin = False
        resp = requests.get("https://api.ebarimt.mn/api/info/check/getTinInfo?regNo=" + vat)
        resp_json = json.loads(resp.text)
        if resp_json:
            partner_tin = resp_json['data']
        return partner_tin

    def ebarimt_send_data(self):

        return self.env['ebarimt.service'].sendData(showInfo=True, host=self.ebarimt_service_host, port = self.ebarimt_service_port)

    def ebarimt_get_information(self):

        return self.env['ebarimt.service'].getInformation(showInfo=True, host=self.ebarimt_service_host, port = self.ebarimt_service_port)