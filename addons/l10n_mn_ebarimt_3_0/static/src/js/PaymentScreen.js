odoo.define('l10n_mn_ebarimt_3_0.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { useState } = owl;
    var rpc = require('web.rpc');

    const EBarimtPaymentScreen = PaymentScreen => class extends PaymentScreen {
        constructor() {
            super(...arguments);
            this.state = useState({ bill_type: null });
        }

        async _isOrderValid() {
            this.currentOrder.bill_type = this.state.bill_type;
            if ((this.currentOrder.bill_type === '5') && !this.currentOrder.get_client()) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    'title': this.env._t('Please select the Customer'),
                    'body': this.env._t('You need to select the customer before you can validate an order.'),
                });
                if (confirmed) {
                    this.selectClient();
                }
                return false;
            } else {
                return super._isOrderValid();
            }
        }

        toggleIsToInvoice() {
            super.toggleIsToInvoice();
            if (this.currentOrder.is_to_invoice() && this.currentOrder.bill_type !== '5') {
                this.currentOrder.bill_type = '5';
            } 

            if (!this.currentOrder.is_to_invoice() && this.currentOrder.bill_type === '5') {
                this.currentOrder.bill_type = '1';
                var rows = $('.partner-detail .flex-row');
                rows.hide();
            }
            this.state.bill_type = this.currentOrder.bill_type;
        }

        changeBillType(event) {
            this.currentOrder.bill_type = event.target.value;
            this.state.bill_type = this.currentOrder.bill_type;
            var currentOrder = this.currentOrder
            var rows = $('.partner-detail .flex-row');
            rows.hide();
            if (this.state.bill_type === '5'){
                this.toggleIsToInvoice();
            }
            if (this.state.bill_type === 'B2B_RECEIPT'){
                var register = $('#register');
                var selected = document.getElementById("bill_type_company").value;
                if (selected === 'B2B_RECEIPT') {
                    $(rows[0]).removeClass('only-child');
                    register.val('');
                    $('.bill-type .company-name').text('');
                    rows.show();
                } else {
                    rows.hide();
                }
                var company  = this.env.pos.company
                // var order = this.currentOrder
                register.keyup(function (e) {
                if (e.keyCode === 13) {
                    var resp = "http://info.ebarimt.mn/rest/merchant/info?regno=" + register.val();

                    rpc.query({
                        model: 'pos.order', 
                        method: 'get_merchant_info', 
                        args: [resp],
                    }).then(function(result){
                        if (result) {
                             var jsonfile = JSON.parse(result);
                            if (register.val() == "") {
                                alert("Татвар төлөгчийн дугаарыг оруулна уу!");
                            }
                            if (register.val() == company.vat) {
                                alert("Та өөрийн компани луу борлуулалт хийж болохгүй!");
                            }
                            if (jsonfile.found == false) {
                                alert(register.val() + " регистрийн дугаартай компани бүртгэлгүй байна!");
                            }
                            document.getElementById("company_name").innerHTML = jsonfile.name;
                            // order.companyName = jsonfile.name;
                            currentOrder.company_name = jsonfile.name;
                        }
                        currentOrder.company_reg = register.val();
                        });

                    }

                    var resp1 = register.val();
                    rpc.query({
                        model: 'res.partner', 
                        method: 'get_customer_tin', 
                        args: [resp1],
                    }).then(function(result1){
                        if (result1) {
                             var jsonfile1 = JSON.parse(result1);
                             console.log('sdfdsfdsf', jsonfile1)
                             currentOrder.customer_tin = jsonfile1;
                        }
                    });

                });

            }
        }
        async _onNewOrder(newOrder) {
           super._onNewOrder(newOrder);
            var rows = $('.partner-detail .flex-row');
            rows.hide();
        }
    
    }

    Registries.Component.extend(PaymentScreen, EBarimtPaymentScreen);

    return PaymentScreen;
});
