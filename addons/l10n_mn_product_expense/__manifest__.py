# -*- coding: utf-8 -*-
{
    'name': "Product Expense",
    'version': '1.0',
    'depends': ['l10n_mn_stock_account','l10n_mn_workflow_config'],
    'author': "Asterisk Technologies LLC",
    'website': "http://www.asterisk-tech.mn",
    'category': 'Product Expense',
    'description': """ Бараа материалын шаардах хуудас
                       - Агуулахын тохиргоонд Барааны шаардахын ажлын урсгал сонгоно
                       - Агуулахын бүртгэл дээр Барааны шаардахын ажлын урсгал сонгоно
                       - Барааны шаардахын бүртгэл ажлын урсгал 
                        """,
    'data': [
        'report/product_expense_report_views_main.xml',
        'report/product_expense_templates.xml',
        'data/mail_templates.xml',
        'data/expense_quantity_data_view.xml',
        'data/product_expense_data_view.xml',
        'data/report_footer_data.xml',
        'security/ir.model.access.csv',
        'security/security_view.xml',
        'views/product_expense_view.xml',
        'views/stock_warehouse_view.xml',
        'views/stock_config_settings_view.xml',
    ],
    'demo': [
    ],
}
