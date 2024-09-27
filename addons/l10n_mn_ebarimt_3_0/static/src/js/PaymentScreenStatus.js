odoo.define('l10n_mn_ebarimt_3_0.PaymentScreenStatus', function(require) {
    'use strict';

    const PaymentScreenStatus = require('point_of_sale.PaymentScreenStatus');
    const Registries = require('point_of_sale.Registries');

    const EBarimtPaymentScreenStatus = PaymentScreenStatus => class extends PaymentScreenStatus {
        get totalDueText() {
            let total = 0;
            if (this.currentOrder.bill_type === '0')
            {
                total = this.currentOrder.get_total_without_tax();
            } else {
                total = this.currentOrder.get_total_with_tax();
            }
            return this.env.pos.format_currency(total + this.currentOrder.get_rounding_applied());
        }
    }

    Registries.Component.extend(PaymentScreenStatus, EBarimtPaymentScreenStatus);

    return PaymentScreenStatus;
});
