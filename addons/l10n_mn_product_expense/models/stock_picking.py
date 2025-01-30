from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    product_expense_id = fields.Many2one('product.expense', 'Product expense')
