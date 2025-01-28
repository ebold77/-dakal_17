# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    expense_id = fields.Many2one('product.expense', 'Expense')

    def check_product_expense(self):
        """Шаардахаас үүссэн хүргэлтийг буцаахад буцаасан тоо хэмжээг шаардахын мөрд тохируулна"""
        for object in self:
            for move in object.move_lines:
                if move.origin_returned_move_id and move.origin_returned_move_id.picking_id.expense_id:
                    for line in move.origin_returned_move_id.picking_id.expense_id.expense_line_ids:
                        if line.product_id.id == move.product_id.id:
                            line.write({'returned_quantity': move.product_qty})

    def _action_done(self):
        """Шаардахаас үүссэн хүргэлт хийгдэхэд шаардахыг 'Дууссан' төлөвт оруулах эсэхийг шалгана"""
        self.check_product_expense()
        res = super(StockPicking, self)._action_done()
        for object in self:
            if object.expense_id:
                object.expense_id.check_done()
        return res