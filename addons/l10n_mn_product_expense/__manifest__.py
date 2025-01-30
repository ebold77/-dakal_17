# -*- coding: utf-8 -*-

{
    'name': 'Product Expense',
    'sequence': 31,
    'category': 'Mongolian Modules',
    'version': '17.0.0.1',
    'website': '',
    'author': 'Enkhbold',
    'description': """
        - Бараа материалын шаардах""",
    'depends': [
        'stock_account',
        'l10n_mn_approval_workflow'
    ],
    'data': [
        'security/security.xml',
        "data/product_expense_data_view.xml",
        "security/ir.model.access.csv",
        "views/transation_values_view.xml",
        "views/product_expense_view.xml",
        "views/product_expense_line_view.xml",
        "views/menu_view.xml",
    ],
    'application': False,
    'license':'LGPL-3',
    'installable': True,
    'auto_install': False
}
