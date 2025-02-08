# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2021 Engineersoft LLC.
#
#    Odoo cloc                 Total line   Other    Code
#    ----------------------------------------------------------------------------
#    es_bank_service_khanbank        1140      203    937
#    ----------------------------------------------------------------------------
#
###################################################################################

{
    'name': ' Bank Synchronization Khan Bank of Mongolia ',
    'category': 'Accounting',
    'website': '',
    'sequence': 10,
    'license': 'Other proprietary',
    'author': 'Enkhbold',
    'support': 'ebold77@gmail.com',
    'version': '17.0.1.1',
    "external_dependencies": {
        "python": [
            'cryptography'],
    },
    'images': ['static/description/banner.png'],
    'depends': ['account_accountant', 'base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/account_journal_dashboard_view.xml',
        'views/account_bank_statement_views.xml',
        'views/account_payment_views.xml',
        'views/khanbank_views.xml',
        'views/res_config_settings.xml',
        'views/currency_views.xml',
        'wizard/khanbank_import.xml',
    ],
    "auto_install": False,
    "installable": True,
    'application': True,
    'price': 114.00,
    'currency': 'USD',
}
