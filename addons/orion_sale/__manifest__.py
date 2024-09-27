# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Orion Sales',
    'version': '17.0.0.1',
    'category': 'Sale',
    'sequence': 200,
    'description': """Orion Online Sales""",
    'website': '',
    'depends': [ 'base', 'sale',],
    'data': [
#         'security/security.xml',
#         'security/ir.model.access.csv',
        'views/res_config_view.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}