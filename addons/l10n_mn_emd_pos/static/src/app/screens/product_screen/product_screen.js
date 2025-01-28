/** @odoo-module */

import { patch } from "@web/core/utils/patch";

import { Chrome } from "@point_of_sale/app/pos_app";

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";

import { _t } from "@web/core/l10n/translation";


patch(ProductScreen.prototype, {
   setup() {
        super.setup();
    	this.pos = usePos();
        this.popup = useService("popup");
        
    },
    _onClickDiscountPharm() {
        this.pos.showTempScreen(
            "EmdDiscountScreenWidget",
            // partnerScreenProps
        );
        // this.showScreen('EmdDiscountScreenWidget');
    }
});