# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2024 Enkhbold
#    Odoo cloc                 Total line   Other    Not count data line    Code
#    ----------------------------------------------------------------------------
#    dakal_mn_emd_pos           25065     361                  23030    1674
#    ----------------------------------------------------------------------------
#
###################################################################################

{
  'name'                 :  'Mongolian EMD System 3.0',
  'summary'              :  'Connect to the Mongolian Health Insurance System.',
  'category'             :  'point_of_sale',
  'version'              :  '17.0.1.1',  
  'author'               :  'EMD',
  'depends'              :  ['base', 'point_of_sale', 'l10n_mn_ebarimt_3_0',
                            ],
  'data'                 :  [
                            'security/security.xml',
                            'security/ir.model.access.csv',
                            'views/insurance_discount_list_view.xml',
                            'views/pos_order_view.xml',
                            'views/pos_config_view.xml',
                            'views/product_view.xml',
                            'views/pos_insurance_sale_view.xml',
                            'views/res_company_view.xml',
                            'wizard/price_comparison_report_wizard.xml',
                            'wizard/pos_session_report_view.xml',
                            ],
  'qweb'                 :  [ ],

  "assets": {
      'web.assets_backend': [
           ],
      'point_of_sale._assets_pos': [
              'l10n_mn_emd_pos/static/src/app/screens/EmdDiscountScreenWidget.xml',
              'l10n_mn_emd_pos/static/src/app/screens/EmdDiscountScreenWidget.js',
              'l10n_mn_emd_pos/static/src/app/screens/product_screen/product_screen.js',
              'l10n_mn_emd_pos/static/src/app/screens/action_pad/action_pad.xml',
              'l10n_mn_emd_pos/static/src/app/screens/action_pad/action_pad.js',
              'l10n_mn_emd_pos/static/src/scss/pos.scss',
              'l10n_mn_emd_pos/static/src/app/store/db.js',
              'l10n_mn_emd_pos/static/src/app/store/models.js',
              # 'l10n_mn_emd_pos/static/src/app/store/product_model.js',
              
      ],
      'web.assets_qweb': [     
            
          
      ],
  },
  'images'               :  ['static/description/emd_logo.png'],
  'installable'          :  True,
  'auto_install'         :  False,
  # 'pre_init_hook'        :  'pre_init_check',
  'license'              :  'LGPL-3',
}

