# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Mongolian Report Base",
    'version': '1.0',
    'depends': ['web'],
    'author': "Asterisk Technologies LLC",
    'website' : 'http://asterisk-tech.mn',
    'category': 'Mongolian Modules',
    'description': """ Тайлангийн тохиргооны модуль
                        - Эксел тайлан гаргах үндсэн харагдац болон функц
                        - OdERP-ийн тайлангийн үндсэн хэлбэржүүлэлтүүдийн эксел хувилбар
                        - Эксел тайлангийн агуулгаас хамаарч нүдний хэмжээг автоматаар тохируулах класс
                        - PDF тайлангийн хэлбэржүүлэлт
                        - Гарын үсгийн тохиргоо --> Менежер групп нэмэгдэнэ
                        - Тайлангуудын гарын үсгийн тохиргооны бүртгэл, тохируулга /Гарын үсгийн тохиргоо --> Менежер/ группт харагдана
    """,
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/report_excel_views.xml',
        'views/report_html_viewer_views.xml',
        # 'views/l10n_mn_report.xml',
        'views/report_config_view.xml',
    ],

    "assets": {
        'web.assets_backend': [
                'l10n_mn_report/static/src/css/handsontable.css',
                'l10n_mn_report/static/src/js/handsontable.js',
                'l10n_mn_report/static/src/js/report_html_viewer.js',
                'l10n_mn_report/static/src/css/report_style.css',
        ],
        'web.assets_qweb': [
            
        ],
    },
    'license': 'GPL-3',
    'installable': True,
    'auto_install': False,
}
