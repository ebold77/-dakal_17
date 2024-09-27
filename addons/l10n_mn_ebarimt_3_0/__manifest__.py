# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2022 Enkhbold
#    ----------------------------------------------------------------------------
#    mongolian_ebarimt           
#    ----------------------------------------------------------------------------
#
###################################################################################

{
  "name"                 :  "Mongolian EBarimt 3.0",
  "summary"              :  "Allows exchange information between POS module and Mongolian Tax Administration.",
  "category"             :  "point_of_sale",
  "version"              :  "17.0.1.2",
  "author"               :  "Enkhbold",
  "depends"              :  ['point_of_sale', 
                            #  'pos_discount',
                            #  'sh_message',
                            ],
  "data"                 :  [
                            #  'data/ebarimt_aimag_district.xml',
                             'data/tax_data.xml',
                             'data/ebarimt_gs1barcode_data.xml',
                             'data/ebarimt_data.xml',
                             'data/report_paperformat_data.xml',
                             'reports/ebarimt_reports.xml',
                             'security/ir.model.access.csv',
                             'security/security.xml',
                            #  'views/pos_assets_common.xml',
                             'views/account_tax_views.xml',
                            #  'views/point_of_sale.xml',
                             'views/account_payment_views.xml',
                             'views/account_move_views.xml',
                             'views/pos_order_views.xml',
                             'views/ebarimt_aimag_district_views.xml',
                             'views/ebarimt_tax_type_views.xml',
                             'views/ebarimt_gs1barcode_views.xml',
                             'views/product_views.xml',
                             'views/pos_config_views.xml',
                             'views/res_config_settings_views.xml',
                             'views/report_receipt.xml',
                             'views/report_payment.xml',
                             'views/report_invoice.xml',
                            #  'wizard/pos_session_report_view.xml',
                            ],

  "qweb"                 :  [
              'static/src/xml/ProductItem.xml',
              'static/src/xml/PaymentScreen.xml',
              'static/src/xml/OrderReceipt.xml',
              'static/src/xml/ClientDetailsEdit.xml',
          ],
 
  "installable"          :  True,
  "auto_install"         :  False,
  "license"              :  "LGPL-3",

  "assets": {
      'web.assets_backend': [
           ],
      'point_of_sale._assets_pos': [
              'l10n_mn_ebarimt_3_0/static/lib/qrcode.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/Chrome.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/ClientDetailsEdit.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/mn_ebarimt.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/OrderReceipt.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/PaymentScreen.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/PaymentScreenStatus.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/ProductScreen.js',
              # 'l10n_mn_ebarimt_3_0/static/src/js/ReceiptScreen.js',
              # 'l10n_mn_ebarimt_3_0/static/src/scss/pos.scss',
              'l10n_mn_ebarimt_3_0/static/src/app/store/models.js',
              'l10n_mn_ebarimt_3_0/static/src/app/product_card/product_card.js',
              'l10n_mn_ebarimt_3_0/static/src/app/product_card/product_card.xml',
      ],
      'web.assets_qweb': [
             'l10n_mn_ebarimt_3_0/static/src/xml/ProductItem.xml',
             'l10n_mn_ebarimt_3_0/static/src/xml/PaymentScreen.xml',
             'l10n_mn_ebarimt_3_0/static/src/xml/OrderReceipt.xml',
             'l10n_mn_ebarimt_3_0/static/src/xml/ClientDetailsEdit.xml',
             
            
          
      ],
  },
 
}