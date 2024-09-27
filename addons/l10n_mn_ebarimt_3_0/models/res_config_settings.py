# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    
    ebarimt_service_host = fields.Char(related='company_id.ebarimt_service_host', readonly=False, string='Ebarimt service address', default= 'localhost')
    ebarimt_service_port = fields.Char(related='company_id.ebarimt_service_port', readonly=False, string='Ebarimt service port', default= '7080')
    aimag_district_id = fields.Many2one('ebarimt.aimag.district', related='company_id.aimag_district_id', string="Aimag/District", readonly=False, required=True, help="This Aimag/District will be assigned by default on new EBarimt put operation.")
    merchant_tin = fields.Char(related='company_id.merchant_tin', readonly=False, string='Merchant Tin')
    def ebarimt_send_data(self):

        return self.env['ebarimt.service'].sendData(showInfo=True, host=self.ebarimt_service_host, port = self.ebarimt_service_port)

    def ebarimt_get_information(self):

        return self.env['ebarimt.service'].getInformation(showInfo=True, host=self.ebarimt_service_host, port = self.ebarimt_service_port)

    def ebarimt_check_api(self):
       
        return self.env['ebarimt.service'].checkApi(showInfo=True, host=self.ebarimt_service_host, port = self.ebarimt_service_port)

        # ebarimt_exchange = self.env['ebarimt.service']
        # return ebarimt_exchange.checkApi(showInfo=True, library_filename=self.pos_library_filename)