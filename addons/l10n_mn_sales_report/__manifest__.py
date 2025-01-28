# -*- coding: utf-8 -*-
# Part of OdErp. See LICENSE file for full copyright and licensing details.
{
    'name': "Mongolian Sales Report",
    'version': '1.0',
    'depends': [
        'l10n_mn_sale_stock',
        'sale_margin'
    ],
    'author': "Asterisk Technologies LLC",
    'website': 'http://asterisk-tech.mn',
    'category': 'Mongolian Sales Module',
    'description': """
        Борлуулалтын дэлгэрэнгүй тайлан
        Борлуулалтын буцаалтын тайлан
    """,
    'data': [
        'wizard/sales_report_view.xml',
        'wizard/sales_refund_report.xml',
        'views/sale_order_view.xml',
        'security/ir.model.access.csv',
    ]
}
