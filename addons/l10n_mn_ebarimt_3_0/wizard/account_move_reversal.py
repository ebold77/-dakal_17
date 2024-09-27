# -*- coding: utf-8 -*-
import json
import requests

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        self.ensure_one()
        ebarimt_url = "http://" +self.company_id.ebarimt_service_host +':'+ self.company_id.ebarimt_service_port+"/rest/receipt"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        refund_data = {}
        moves = self.move_ids

        # Create default values.
        default_values_list = []
        for move in moves:
            refund_data['id'] = move.bill_id
            refund_data['date'] = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('refund_data============>>', refund_data)
        data_json = json.dumps(refund_data)
        response = requests.delete(url=ebarimt_url, data=data_json, headers=headers)
        if response.text:
            print('response==============>>>', response.text)
            try:
                data = json.loads(response.text)
            except Exception as e:
                raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e)

            # data_json = json.dumps(data)
            if data['status'] == 'ERROR':
                raise ValidationError(data['message'])
        
        reverse = super(AccountMoveReversal, self).reverse_moves()

        
        return reverse
    