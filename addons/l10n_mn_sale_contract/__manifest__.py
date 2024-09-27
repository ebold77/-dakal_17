# -*- coding: utf-8 -*-

{
    "name": "Борлуулалтын гэрээ",
    "version": "17.1.0",
    "author": "Enkhbold",
    "description": """
        - Борлуулалтын гэрээний бүртгэл, Гүйцэтгэлийн хяналт
""",
    'website': "",
    "category": "Sales",
    'license':'LGPL-3',
    "depends": ['l10n_mn_sale'],
    "init": [],
    "data": [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
        'views/sale_contract_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}