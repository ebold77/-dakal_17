/** @odoo-module */

import { patch } from "@web/core/utils/patch";

import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { usePos } from "@point_of_sale/app/store/pos_hook";

import { _t } from "@web/core/l10n/translation";


patch(ActionpadWidget.prototype, {
   setup() {
        super.setup();
    	this.pos = usePos();
        
    },
    _onClickDiscountPharm() {
        console.log('click Discount EMD')
        this.pos.showScreen('EmdDiscountScreenWidget');
    }
});