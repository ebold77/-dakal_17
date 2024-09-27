/** @odoo-module **/
import { Product } from "@pos_self_order/app/models/product";
import { patch } from "@web/core/utils/patch";

patch(Product.prototype, {

    setup({ id, name, tax_type, ebarimt_gs1barcode_id }) {
        this.id = id;
        this.name = name;
        this.tax_type = tax_type;
        this.ebarimt_gs1barcode_id = ebarimt_gs1barcode_id;
    }
});
