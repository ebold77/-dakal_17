import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    reg_no = fields.Char('Register No', related='partner_id.vat')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(AccountMove, self)._onchange_partner_id()
        
        self.reg_no = self.partner_id.vat