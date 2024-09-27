import collections
import requests, json
import logging

from odoo import models, fields, _
from odoo.tools import populate
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    
    box_qty = fields.Integer('Quantity in the Box', default=1)

class ProductProduct(models.Model):
    _inherit = "product.product"

    
    box_qty = fields.Integer('Quantity in the Box', related='product_tmpl_id.box_qty',)