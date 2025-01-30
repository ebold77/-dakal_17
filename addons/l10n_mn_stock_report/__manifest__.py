# -*- coding: utf-8 -*-
##############################################################################
#

{
    "name": "Stock Report",
    'version': '17.0.0.1',
    "author": "Enkhbold",
    "description": """
            Бараа материалын дэлгэрэнгүй тайлан
""",
    'website': '',
    "category": "Stock Report",
    "depends": [
        'stock',
    ],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/stock_report_detail_view.xml',
        'wizard/product_move_detail_wizard_view.xml',
        'wizard/report_expense_ledger_view.xml',
        'wizard/report_income_ledger_view.xml',
        'wizard/report_product_analyses.xml',
        'views/menu_view.xml',
    ],
    "demo_xml": [],
    'license':'LGPL-3',
    "active": False,
    "installable": True,
}
