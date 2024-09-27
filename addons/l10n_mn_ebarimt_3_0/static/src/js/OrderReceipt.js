odoo.define('l10n_mn_ebarimt_3_0.OrderReceipt', function(require) {
    'use strict';

    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');

    const EBarimtOrderReceipt = OrderReceipt => class extends OrderReceipt {
        get receiptEnv () {
            let receipt_render_env = super.receiptEnv;
            let order = this.env.pos.get_order();

            receipt_render_env.receipt.bill_type = order.bill_type;
            receipt_render_env.receipt.company_reg = order.company_reg;
            receipt_render_env.receipt.company_name = order.company_name;

            return receipt_render_env;
        }
    }

    Registries.Component.extend(OrderReceipt, EBarimtOrderReceipt);

    return OrderReceipt;
});