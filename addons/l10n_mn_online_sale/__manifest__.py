# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mongolian Online Sales',
    'version': '17.0.0.1',
    'category': 'Sale',
    'sequence': 335,
    'description': """Mongolian Online Sales""",
    'license':'LGPL-3',
    'website': '',
    'depends': [ 'base', 'sale', 'l10n_mn', 'l10n_mn_stock_dakal'],
    'data': [
#         'security/security.xml',
#         'security/ir.model.access.csv',
        # 'data/mail_data.xml',
        
        'views/res_config_view.xml',

        
        # 'wizard/invoice_warehouse_settings_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}