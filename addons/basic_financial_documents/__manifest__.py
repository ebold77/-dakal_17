# -*- coding: utf-8 -*-

{
    'name': "Basic Financial Documents",
    'version': '17.0.0.1',
    'author': 'Enkhbold',
    'category': 'Base',
    'website': '',
    'sequence': 2,
    'summary': """
    Parent Children relation tree..
    """,
    'description': """
    basic financial documents
    """,
    'price': 0.00,
    'currency': 'EUR',
    'depends': [
        'account',
    ],
    'images': ['static/description/icon.png'],
    'data': [
        'views/account_bank_statement_view.xml',
        'report/print_report_view.xml',
        'report/print_cash_order_view.xml',
        'report/payment_report_view.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}