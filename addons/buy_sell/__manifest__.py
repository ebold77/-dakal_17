# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Buy and Sell',
    'version': '17.0.0.1',
    'category': 'Sale',
    'sequence': 335,
    'description': """ Buy and Sell""",
    'website': '',
    'depends': [ 'base', 'account', 'sale', 'sale_purchase', 'stock', 'purchase'],
    'data': [
        # "views/web_assets.xml",
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/barter_report.xml',
        'report/ir_actions_report.xml',
        'data/buy_sell_data.xml',
        'views/menu.xml',
        'views/buy_sell_view.xml',
        'views/res_company_view.xml',
        'views/buy_sell_config_view.xml',
        'views/stock_warehouse_view.xml',
        'views/purchase_view.xml',
        # 'report/report_view.xml',
        'wizard/sale_purchase_order_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.report_assets_common': [
            'buy_sell/static/src/scss/reports_templates.scss',
        ],
        
    },
}
