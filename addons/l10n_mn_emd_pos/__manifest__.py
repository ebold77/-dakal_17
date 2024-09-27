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
                            'views/web_assets_backend.xml',
                            'views/pos_config_view.xml',
                            'views/product_view.xml',
                            'views/pos_insurance_sale_view.xml',
                            'views/res_company_view.xml',
                            'wizard/price_comparison_report_wizard.xml',
                            'wizard/pos_session_report_view.xml',
                            ],
  'qweb'                 :  [
                            'static/src/xml/EmdDiscountScreenWidget.xml',
                            'static/src/xml/ActionpadWidget.xml',
                            'static/src/xml/OrderDetails.xml',
                            'static/src/xml/ProductItem.xml',
                            'static/src/xml/OrderReceipt.xml',
                            ],
  'images'               :  ['static/description/emd_logo.png'],
  'installable'          :  True,
  'auto_install'         :  False,
  'pre_init_hook'        :  'pre_init_check',
  'license'              :  'LGPL-3',
}

