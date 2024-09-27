# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class EBarimt_GS1Barcode(models.Model):
    _name = 'ebarimt.gs1barcode'
    _description = "EBarimt GS1 Barcode"

    name = fields.Char(string='Name', required=True)
    display_name = fields.Char('Full Name', compute='_compute_display_name')
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer('Sequence', index=True, help="Gives the sequence order when displaying a list of gs1 barcodes.")
    parent_id = fields.Many2one(string='Parent Code', comodel_name='ebarimt.gs1barcode', index=True, ondelete='cascade')
    child_ids = fields.One2many(string='Child Codes', comodel_name='ebarimt.gs1barcode', inverse_name='parent_id')
    parent_left = fields.Integer('Left Parent', index=True)
    parent_right = fields.Integer('Right Parent', index=True)
    parent_path = fields.Char(index=True, unaccent=False)
    
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_left'
    
    # _constraints = [(models.BaseModel._check_recursion, 'Error! You cannot create recursive gs1 barcode.', ['parent_id'])]

    @api.depends('name', 'parent_id.name')
    def _compute_display_name(self):
        for gs1barcode in self:
            """ Return the gs1barcode's display name, including their direct parent. """
            if gs1barcode.parent_id.display_name:
                gs1barcode.display_name = '%s/%s' % (gs1barcode.parent_id.display_name, gs1barcode.name)
            else:
                gs1barcode.display_name = gs1barcode.name

    def name_get(self):
        """ Return the gs1barcode's display name, including their direct parent. """
        res = {}
        for record in self:
            current = record
            name = current.name
            while current.parent_id:
                name = '%s / %s' % (current.parent_id.name, name)
                current = current.parent_id
            res[record.id] = name

        return  [(record.id,  record.name) for record in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symmetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        gs1barcodes = self.search(args, limit=limit)
        return gs1barcodes.name_get()
