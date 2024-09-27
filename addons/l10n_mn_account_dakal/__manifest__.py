# -*- coding: utf-8 -*-

{
    'name': 'Accounting for DakalPharma LLC',
    'version': '17.0.0.0',
    'summary': 'Invoice buttons hiden for sale\'s manager',
    'category': 'Tools',
    'description': """
        Accounting for DakalPharma LLC
    """,
    'license':'OPL-1',
    'author': 'Enkhbold',
    'website': '',
    'depends': ['base', 'account'],
    'data': [

        "views/account_move_views.xml",
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/web2sms_view.xml",
        'wizard/send_multi_sms_wizard.xml',
        'wizard/set_credit_limit_wizard.xml'
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}