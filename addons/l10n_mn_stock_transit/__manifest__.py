# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mongolian Stock Transit',
    'version': '17.0.0.1',
    'category': 'Stock',
    'license':'LGPL-3',
    'author': 'Enkhbold',
    'sequence': 335,
    'description': """Mongolian Stock""",
    'website': '',
    'depends': [ 'base', 'stock'],
    'data': [
# #         'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/stock_picking_view.xml',
        'views/product_view.xml',
        'views/stock_transit_order_view.xml',
        'report/ir_actions_report.xml',
        'report/stock_transit_order_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}