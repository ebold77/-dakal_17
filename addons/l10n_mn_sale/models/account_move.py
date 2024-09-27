import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse' )
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")