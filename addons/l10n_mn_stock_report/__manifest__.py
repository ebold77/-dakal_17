# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Mongolian Stock Report",
    'version': '1.0',
    'depends': ['l10n_mn_stock'],
    'author': "Asterisk Technologies LLC",
    'category': 'Mongolian Modules',
    'description': """ Агуулахын тайлангууд
                - Бараа материалын тайлан
                    - Агуулах -- Тайлан -- Бараа материалын тайлан
                - Нөхөн дүүргэлтийн эксел тайлан
                    - Агуулах -- Тайлан -- Нөхөн дүүргэлтийн тайлан
                - Агуулахын баримтууд
                    - Агуулах -> Тайлан -> Бүртгэл хяналтын баримт
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/res_config_settings_view.xml',
        'wizard/product_ledger_report_view.xml',
        'views/product_report_view.xml',
        'report/stock_transit_report_view.xml',
        'wizard/product_move_check_report_view.xml',
        'report/product_move_check_report_view.xml',
    ],
    'license': 'GPL-3',
    'installable': True,
    'auto_install': False
}