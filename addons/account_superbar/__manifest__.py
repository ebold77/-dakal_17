# -*- coding: utf-8 -*-

{
    'name': "Account superbar",
    'version': '17.0.0.1',
    'author': 'Enkhbold',
    'category': 'Base',
    'website': '',
    'sequence': 2,
    'summary': """
    Parent Children relation tree..
    """,
    'description': """
    Superbar
    """,
    'price': 0.00,
    'currency': 'EUR',
    'depends': [
        'sale_management',
    ],
    'images': ['static/description/icon.png'],
    'data': [
        'views/account_views.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
