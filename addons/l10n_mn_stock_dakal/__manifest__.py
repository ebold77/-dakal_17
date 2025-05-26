# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mongolian Stock',
    'version': '17.0.0.1',
    'category': 'Stock',
    'license':'OPL-1',
    'author': 'Enkhbold',
    'sequence': 335,
    'description': """Mongolian Stock""",
    'website': '',
    'depends': [ 'base', 'stock', 'sale_stock', 'l10n_mn', 'hr', 'l10n_mn_stock_transit'],
    'data': [
#         'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        'views/account_move_view.xml',
        'views/sale_order_view.xml',
        'views/licemed_registration_view.xml',
        'views/product_general_category_view.xml',
        'views/product_view.xml',
        'views/stock_lot_view.xml',
        'wizard/stock_inventory_statement_view.xml',
        'wizard/stock_product_balance_report_view.xml',
        # 'wizard/lot_stock_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}