# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mongolian Sales Report',
    'version': '17.0.0.1',
    'category': 'Sale',
    'sequence': 335,
    'description': """Mongolian Sales Report""",
    'license':'LGPL-3',
    'website': '',
    'depends': [ 'base', 'sale', 'sales_team','l10n_mn'],
    'data': [
#         'security/security.xml',
#         'security/ir.model.access.csv',
        'wizard/report_product_sales_view.xml',
        'wizard/sales_performance_report_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}
