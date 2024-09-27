odoo.define('l10n_mn_health_insurance_pos_3_0.DB', function (require) {
    "use strict";
        
        var PosDB = require('point_of_sale.DB');
        PosDB.DB = PosDB.include({
            get_product_by_emd_list: function(category_id){
                console.log('call emd list', category_id)
                var product_ids  = this.product_by_category_id[category_id];
                var list = [];
                
                if (product_ids) {
                    for (var i = 0, len = product_ids.length; i < len; i++) {
                        var product = this.product_by_id[product_ids[i]]
                        
                        if (product.insurance_list_id){
                            list.push(product);
                        }
                    }
                }
                return list;
            }
        
        });
    });
        