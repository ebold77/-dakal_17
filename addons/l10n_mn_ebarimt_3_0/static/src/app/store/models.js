/** @odoo-module **/
import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { random5Chars, uuidv4, qrCodeSrc, constructFullProductName } from "@point_of_sale/utils";
import { patch } from "@web/core/utils/patch";
import {onMounted} from "@odoo/owl";
import { ConnectionLostError } from "@web/core/network/rpc_service";

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
        this.company_name = json.company_name;
        this.customer_tin = json.customer_tin;
        this.company_reg = json.company_reg;
        this.bill_id = json.bill_id;
        // this.vat_number = json.vat_number;
        this.lottery = json.lottery;
        this.qrdata = json.qrdata;
        // this.nhat_amount = json.nhat_amount;
    },

    set_company_reg: function(value){
        this.company_reg = value;
        this.trigger('change',this);
    },
    get_company_reg: function(){
        return this.company_reg;
    },
    set_order_partner_name: function(value){
        this.company_name = value;
        this.trigger('change',this);
    },
    get_order_partner_name: function(){
        return this.company_name;
    },
    set_customer_tin: function(value){
        this.customer_tin = value;
        this.trigger('change',this);
    },
    get_customer_tin: function(){
        return this.customer_tin;
    },

    set_bill_type: function(value){
        this.bill_type = value;
        this.trigger('change',this);
    },
    get_bill_type: function(){
        return this.bill_type;
    },
    set_bill_id: function(value){
        this.bill_id = value;
    },
    get_bill_id: function(){
        return this.bill_id;
    },
    set_lottery: function(value){
        this.lottery = value;
    },
    get_lottery: function(){
        return this.lottery;
    },
    set_qrdata: function(value){
        this.qrdata = value;
    },
    get_qrdata: function(){
        return this.qrdata;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (!this.bill_type) { this.bill_type = 'B2C_RECEIPT'; }
        json.bill_type = this.bill_type;
        json.company_reg = this.company_reg;
        json.company_name = this.company_name;
        json.customer_tin = this.customer_tin;
        if (this.bill_type === '0'){
            json.amount_total = this.get_total_without_tax();
            json.amount_tax = 0;
        }
        return json;
    },

    export_for_printing() {
        // var receipt = super.prototype.export_for_printing.apply(this,arguments);
        const receipt = super.export_for_printing(...arguments);
        if (!this.bill_type) { this.bill_type = 'B2C_RECEIPT'; }
        receipt.bill_type = this.bill_type;
        receipt.company_name = this.company_name;
        receipt.company_reg = this.company_reg;
        receipt.bill_id = this.bill_id;
        receipt.lottery = this.lottery;
        receipt.qrdata = this.qrdata &&
        qrCodeSrc(
            `${this.pos.base_url}/pos/ticket/validate?access_token=${this.access_token}`
        );
        if (this.bill_type === '0'){
            receipt.total_with_tax = this.get_total_without_tax();
            receipt.total_tax = 0;
            receipt.tax_details = [];
        }
        return receipt;
    },

});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
    },

    export_as_JSON() {
        // var json = super.prototype.export_as_JSON.apply(this,arguments);
        const json = super.export_as_JSON(...arguments);
        if (this.order.bill_type === '0'){
            json.price_subtotal_incl = this.get_price_without_tax();
            json.tax_ids = [];
        }
        return json;
    },

    export_for_printing() {
        // var json = super.prototype.export_for_printing.apply(this,arguments);
        const json = super.export_for_printing(...arguments);
        json.tax_details = this.get_tax_details();
        json.product_id = this.product.id;
        if (this.order.bill_type === '0'){
            json.price_with_tax = this.get_price_without_tax();
        }
        return json;
    },

});

patch(Payment.prototype, {
    /**
     * Override this method to be able to show the 'Adjust Authorisation' button
     * on a validated payment_line and to show the tip screen which allow
     * tipping even after payment. By default, this returns true for all
     * non-cash payment.
     */
    setup() {
        super.setup(...arguments);
    },
    export_for_printing() {
        const json = super.export_for_printing(...arguments);
        json.payment_method_id = this.payment_method.id;
        return json;
    },
});


patch(PosStore.prototype, {

    async _flush_orders(orders, options = {}) {
        try {
            const server_ids = await this._save_to_server(orders, options);
            for (let i = 0; i < server_ids.length; i++) {
                this.validated_orders_name_server_id_map[server_ids[i].pos_reference] =
                    server_ids[i].id;
                    this.send_ebarimt(server_ids[i])      
                }
            return server_ids;
        } catch (error) {
            if (!(error instanceof ConnectionLostError) && !options.printedOrders) {
                for (const order of orders) {
                    const reactiveOrder = this.orders.find((o) => o.uid === order.id);
                    reactiveOrder.finalized = false;
                    this.db.remove_order(reactiveOrder.uid);
                    this.db.save_unpaid_order(reactiveOrder);
                }
                this.set_synch("connected");
            }
            throw error;
        } finally {
            this._after_flush_orders(orders);
        }
    },
    async send_ebarimt(server_ids) {
        try {
            if (server_ids){
                    const vat_data = await this.orm.call("pos.order", "get_ebarimt", [
                        server_ids
                            ]);
                    this.selectedOrder.set_bill_id(vat_data[0]['bill_id'])
                    this.selectedOrder.set_qrdata(vat_data[0]['qr_data'])
                    if (this.selectedOrder.bill_type == 'B2C_RECEIPT'){
                        this.selectedOrder.set_lottery(vat_data[0]['lottery'])
                    }
                    
                    
                    
                }
            
        } catch (error) {
            console.log('error ========', error);
        }   
        
    },
});