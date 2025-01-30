/** @odoo-module **/
import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";

patch(PosDB.prototype, {

    get_product_by_emd_list: function(category_id){
        var product_ids  = this.product_by_category_id[category_id];
        var list = [];
        
        if (product_ids) {
            for (var i = 0, len = product_ids.length; i < len; i++) {
                var product = this.product_by_id[product_ids[i]]
                if (product.emd_insurance_list_id){
                    list.push(product);
                }
            }
        }
        return list;
    },
    
    get_product_by_all: function(category_id){
        var product_ids  = this.product_by_category_id[category_id];
        
        var list = [];
        
        if (product_ids) {
            for (var i = 0, len = product_ids.length; i < len; i++) {
                var product = this.product_by_id[product_ids[i]]
                list.push(product);
            }
        }
        return list;
    }
});

