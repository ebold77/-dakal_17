/** @odoo-module **/
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { random5Chars, uuidv4, qrCodeSrc, constructFullProductName } from "@point_of_sale/utils";
import { patch } from "@web/core/utils/patch";
import {onMounted} from "@odoo/owl";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { floatIsZero, roundPrecision as round_pr } from "@web/core/utils/numbers";

patch(Order.prototype, {
    
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.bill_type = this.get_bill_type() || 'B2C_RECEIPT';
        // this.companyName = '';
        this.company_reg = '';
        this.company_name = '';
        this.customer_tin = '';

    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.emd_discount_amount = 0;
        this.receipt_number = 0;
        this.pharmDiscount = {}
    },

    set_receiptNumber: function (receiptNumber) {
        this.receipt_number = receiptNumber;
     
    },
    set_prescriptionType: function (prescriptionType) {
        this.prescriptionType = prescriptionType;
    
    },
    set_lastName: function (lastName) {
            this.last_name = lastName;
        
    },
    set_firstName: function (firstName) {
            this.first_name = firstName;
        
    },
    set_register: function (register) {
            this.register = register;
        
    },
    set_receipt_id: function (receipt_id) {
            this.receipt_id = receipt_id;
        
    },

    async add_product(product, options) {
        if (
            this.pos.doNotAllowRefundAndSales() &&
            this._isRefundOrder() &&
            (!options.quantity || options.quantity > 0)
        ) {
            this.pos.env.services.popup.add(ErrorPopup, {
                title: _t("Refund and Sales not allowed"),
                body: _t("It is not allowed to mix refunds and sales"),
            });
            return;
        }
        if (this._printed) {
            // when adding product with a barcode while being in receipt screen
            this.pos.removeOrder(this);
            return await this.pos.add_new_order().add_product(product, options);
        }
        this.assert_editable();
        options = options || {};
        const quantity = options.quantity ? options.quantity : 1;
        const detail_id = options.detailId
        const line = new Orderline(
            { env: this.env },
            { pos: this.pos, order: this, product: product, quantity: quantity}
        );

        line.set_detail_id(options.detailId)
        this.fix_tax_included_price(line);
        
        this.set_orderline_options(line, options);
        line.set_full_product_name();
        var to_merge_orderline;
        for (var i = 0; i < this.orderlines.length; i++) {
            if (this.orderlines.at(i).can_be_merged_with(line) && options.merge !== false) {
                to_merge_orderline = this.orderlines.at(i);
            }
        }
        if (to_merge_orderline) {
            to_merge_orderline.merge(line);
            this.select_orderline(to_merge_orderline);
        } else {
            this.add_orderline(line);
            this.select_orderline(this.get_last_orderline());
        }

        if (options.draftPackLotLines) {
            this.selected_orderline.setPackLotLines({
                ...options.draftPackLotLines,
                setQuantity: options.quantity === undefined,
            });
        }

        if (options.comboLines?.length) {
            await this.addComboLines(line, options);
            // Make sure the combo parent is selected.
            this.select_orderline(line);
        }
        this.hasJustAddedProduct = true;
        clearTimeout(this.productReminderTimeout);
        this.productReminderTimeout = setTimeout(() => {
            this.hasJustAddedProduct = false;
        }, 3000);
        return line;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.receipt_number = this.receipt_number;
        json.last_name = this.last_name;
        json.first_name = this.first_name;
        json.register = this.register;
        json.receipt_id = this.receipt_id;
        json.prescriptionType = this.prescriptionType;
        return json;
    },

    export_for_printing() {
        // var receipt = super.prototype.export_for_printing.apply(this,arguments);
        const receipt = super.export_for_printing(...arguments);
        // receipt.company.ph_mobile = this.pos.company.ph_mobile;
        return receipt;
    },

});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.emd_discount = 0;
        this.emd_discount_str = '0';
        this.emd_discount_qty = 0;
    },

    set_detail_id: function (detail_id) {
        this.order.assert_editable();
        this.detail_id = detail_id;
    },
    // sets a emd discount [0,100]%
    set_emd_discount: function(discount){
        var disc = Math.min(Math.max(parseFloat(discount) ||  0, 0),100);
        this.emd_discount = disc;
        this.emd_discount_str = '' + disc;
        
    },
    // returns the emd discount [0,100]%
    get_emd_discount: function(){
        return this.emd_discount || 0;
    },
    get_emd_discount_str: function(){
        return this.emd_discount_str || '';
    },
    get_unit_price_after_discount: function(){
        return this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
    },
    
    // returns the emd discount amount from discount percent
    get_emd_discount_amount: function(){
        if (this.get_emd_discount() != 0){

            return this.get_unit_price_after_discount() * (this.get_emd_discount() / 100.0);
        }else{
            return 0;
        }
    },

    get_full_product_name: function () {
        if (this.full_product_name) {
            return this.full_product_name
        }
        var full_name = '['+ this.product.default_code + '] '+ this.product.display_name;
        if (this.description) {
            full_name += ` (${this.description})`;
        }
        return full_name;
    },

    export_as_JSON() {
        // var json = super.prototype.export_as_JSON.apply(this,arguments);
        const json = super.export_as_JSON(...arguments);
        json['emd_discount'] = this.get_emd_discount();
        json['detail_id'] = this.detail_id;
        return json;
    },


});

