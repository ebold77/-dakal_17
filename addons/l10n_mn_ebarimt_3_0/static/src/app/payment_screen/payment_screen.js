/** @odoo-module */

import { patch } from "@web/core/utils/patch";

import { Chrome } from "@point_of_sale/app/pos_app";

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";

import { _t } from "@web/core/l10n/translation";


patch(PaymentScreen.prototype, {
   setup() {
        super.setup();
    	this.pos = usePos();
        this.popup = useService("popup");
        
    },
    
    
    async afterOrderValidation(suggestToSync = true) {
        // Remove the order from the local storage so that when we refresh the page, the order
        // won't be there
        this.pos.db.remove_unpaid_order(this.currentOrder);

        // Ask the user to sync the remaining unsynced orders.
        if (suggestToSync && this.pos.db.get_orders().length) {
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t("Remaining unsynced orders"),
                body: _t("There are unsynced orders. Do you want to sync these orders?"),
            });
            if (confirmed) {
                // NOTE: Not yet sure if this should be awaited or not.
                // If awaited, some operations like changing screen
                // might not work.
                this.pos.push_orders();
            }
        }
        // Always show the next screen regardless of error since pos has to
        // continue working even offline.
        let nextScreen = this.nextScreen;

        if (
            nextScreen === "ReceiptScreen" &&
            !this.currentOrder._printed &&
            this.pos.config.iface_print_auto
        ) {
            const invoiced_finalized = this.currentOrder.is_to_invoice()
                ? this.currentOrder.finalized
                : true;

            if (this.hardwareProxy.printer && invoiced_finalized) {
				
                const printResult = await this.printer.print(OrderReceipt, {
                    data: this.pos.get_order().export_for_printing(),
                    formatCurrency: this.env.utils.formatCurrency,
                });

                if (printResult && this.pos.config.iface_print_skip_screen) {
                    this.pos.removeOrder(this.currentOrder);
                    this.pos.add_new_order();
                    nextScreen = "ProductScreen";
                }
            }
        }
		
		// if (this.pos.config.is_ebarimt_print == true){
        const currentPosOrder = this.pos.get_order();
     
        this.pos.showScreen(nextScreen);
	      
     },
     

    async onCompanyClick(event) {
        this.selectedValue = event.target.value;
        if (this.selectedValue =='company'){     
		 	const currentPosOrder = this.pos.get_order();
		 	if (!currentPosOrder) return;
			const { confirmed, payload: vatnumber } = await this.env.services.popup.add(TextInputPopup, {
				confirmText: _t("Шалгах"),
				closePopup: _t("Хаах"),
            	title: _t("Татвар төлөгчийн дугаар оруулна уу"),
	        });
	
	        if (confirmed) {
				const vat_partner_name = await this.orm.call("pos.order", "get_company_name", [
                vatnumber,
            ]);
            
            if (vat_partner_name===''){
				this.env.services.popup.add(ErrorPopup,{
					title: _t('Компани Олдсонгүй'),
					});
					var lists = document.getElementById("companyorself");
					lists.value = 'B2B_RECEIPT';
			}
			else{
                const customer_tin = await this.orm.call("pos.order", "get_customer_tin", [
                    vatnumber,
                ]);

				var lists = document.getElementById("companyorself");
	  	    	$(".vat_text").show();
	  	        $(".com_name").show();
                $('.com_name').html(vat_partner_name);
	  	        lists.value = 'B2B_RECEIPT';
	  	        currentPosOrder.bill_type ='B2B_RECEIPT';
	  	        currentPosOrder.company_name = vat_partner_name;
	  	        currentPosOrder.company_reg = vatnumber;
                currentPosOrder.customer_tin = customer_tin['data'];
			}
	        }
	    } 
        else{
            $(".vat_text").hide();
	  	    $(".com_name").hide();
        }
	}
		 
		 
    
	
	
});
