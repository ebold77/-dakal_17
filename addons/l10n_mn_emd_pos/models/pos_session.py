# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = 'pos.session'

   
    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('emd_insurance_list_id')
        result['search_params']['fields'].append('package_qty')
     
        return result 

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result += ['product.product']

        return result