# -*- coding: utf-8 -*-
import logging
import time
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    transit_order_id = fields.Many2one('stock.transit.order', string='Transit Order')

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        self.after_done()
        return res

    def after_done(self):
        ''' Барааны баримт дууссаны дараа тухайн баримтаас
            хамааралтай бусад процессуудыг шалгана.
        '''
        for pick in self:
            if pick.transit_order_id:
                pick.transit_order_id.check_done()
        return True