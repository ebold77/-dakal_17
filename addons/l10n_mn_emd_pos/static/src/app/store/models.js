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
        receipt.company.ph_mobile = this.pos.company.ph_mobile;
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

    set_quantity: function (quantity) {
        this.order.assert_editable();
        if (quantity === 'remove') {
            this.order.remove_orderline(this);
            return;
        } else {
            var quant = parseFloat(quantity) || 0;
            this.quantity = round_pr(quant, 0.00000001);
            this.quantityStr = '' + this.quantity;
        }
        
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

