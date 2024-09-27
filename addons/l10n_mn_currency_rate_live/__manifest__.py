# -*- coding: utf-8 -*-

{
    'name': 'Mongolian currency rate live',
    'description': """
Account module
====================
- Download currency rate from mongolbank
    """,
    'version': '17.0.0.1',
    'category': 'Account',
    'depends': [
        'account',
    ],
    'data': [
        'data/cron.xml',
    ],
    'application': True,
    'license':'LGPL-3',
    'installable': True,
    'auto_install': False,
}
