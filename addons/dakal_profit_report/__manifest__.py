# -*- coding: utf-8 -*-

{
    'name': "Profit Report",
    'version': '17.0.0.1',
    'author': 'Enkhbold',
    'category': 'Accounting',
    'website': '',
    'sequence': 2,
    'summary': """
    Profit Report..
    """,
    'description': """
    Profit Report
    """,
    'price': 0.00,
    'currency': 'EUR',
    'depends': [
        'account', 'sale','stock',
    ],
    'images': ['static/description/icon.png'],
    'data': [
        'wizard/profit_report_view.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
