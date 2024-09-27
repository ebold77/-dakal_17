# -*- coding: utf-8 -*-
import requests
import json

from odoo import api, models, fields, _

class ebarimt_aimag_district(models.Model):
    _name = 'ebarimt.aimag.district'
    _description = 'EBarimt Aimag/District'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)

    # _sql_constraints = [('code_ebarimt_aimag_district_uniq', 'unique (code)', 'The code of the ebarimt Aimag/District must be unique!')]

    def get_district_list(self):
       
        urlInput = 'https://api.ebarimt.mn/api/info/check/getBranchInfo'

        resp = requests.get(url=urlInput)
        data = None
        
        if resp:
            try:
                data = json.loads(resp.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            # data_json = json.dumps(data)
            for district in data['data']:
                vals= {
                    'name': district['branchName']+' - '+ district['subBranchName'],
                    'code': district['branchCode'] + district['subBranchCode']
                }
                
                aimag_dist = self.env['ebarimt.aimag.district'].create(vals)
        


