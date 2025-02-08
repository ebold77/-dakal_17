# -*- coding: utf-8 -*-

{
    'name': 'Approval workflow',
    'sequence': 31,
    'category': 'Mongolian Modules',
    'version': '17.0.0.1',
    'website': '',
    'author': 'Enkhbold',
    'description': """
        Configuration for dynamic approval workflow""",
    'depends': [
        'hr',
        'product',
    ],
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/approval_workflow_views.xml",
    ],
    'application': False,
    'license':'LGPL-3',
    'installable': True,
    'auto_install': False
}
