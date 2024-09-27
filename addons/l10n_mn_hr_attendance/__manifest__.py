# -*- coding: utf-8 -*-
{
    "name":     "Mongolian HR Attendance",
    "version":  "17.0.0.1",
    "depends":  [
                 "hr_attendance",
                ],
    "author":   "Enkhbold",
    "website":  "",
    "category":    "Mongolian HR Modules",
    "description": """
       
       Ирцийн бүртгэл, тайлан, тохиргоо
       
      
    """,
    "data": [
            "security/hr_attendance_security.xml",
            "security/ir.model.access.csv",
            "views/hr_attendance_raw_data_views.xml",
            "views/hr_attendance_device_views.xml",
            # "views/res_config_views.xml",
            "views/hr_employee_views.xml",
            "views/hr_only_my_attendance_view.xml",
            "views/hr_attendance_views.xml",
            "views/hr_employee_attendance_device_views.xml",
            "wizard/hr_attendance_download.xml",
            # "wizard/hr_attendance_report_view.xml",
            "data/auto_download_attendance_cron.xml",
        ],
    "external_dependencies": {
        "python": ["zk"],
    },
    "installable"          :  True,
  "auto_install"         :  False,
  "license"              :  "LGPL-3",

  "assets": {
      'web.assets_backend': [
            # 'l10n_mn_hr_attendance/static/src/js/basic_view.js'
           ],
      
      'web.assets_qweb': [
                       
          
      ],
  },
    
}
