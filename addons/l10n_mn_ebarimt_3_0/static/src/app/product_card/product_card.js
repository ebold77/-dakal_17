/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async addProductToCurrentOrder(...args) {
        
            await super.addProductToCurrentOrder(...args)
        
    },
});