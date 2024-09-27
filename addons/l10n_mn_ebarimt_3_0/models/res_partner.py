# -*- coding: utf-8 -*-
import requests
import json

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"


    @api.model
    def get_merchant_info(self, urlInput):
        """ Get metchant info from ebarimt REST api """
        resp = requests.get(url=urlInput)
        data = None
        print('resp==============>>>', resp)
        if resp:
            try:
                data = json.loads(resp.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            data_json = json.dumps(data)
            return data_json


    @api.model
    def get_customer_tin(self, vat):
        """ Get metchant info from ebarimt REST api """
        urlInput = "https://api.ebarimt.mn/api/info/check/getTinInfo?regNo=" + vat

        resp1 = requests.get(url=urlInput)
        data = None
        print('resp==============>>>', resp1)
        if resp1:
            try:
                data_json = json.loads(resp1.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            # data_json = json.dumps(data)
            return data_json['data']