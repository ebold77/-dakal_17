# -*- coding: utf-8 -*-

{
    'name': 'Website attachments',
    'category': 'Hidden',
    'version': '1.0',
    'author': 'Enkhbold',
    'description': """
                Adds field attachments to contact us form.
        """,
    'depends': [
        'website_crm',
        'crm',
        'website_partner',
    ],
    'data': [
        'views/website_crm_templates.xml',
        
    ],
    'auto_install': True,
    'assets': {
        'web.assets_backend': [
            'l10n_mn_website_form_attachment/static/src/js/website_crm_editor.js',
        ],
    },
    'license': 'LGPL-3',
}
