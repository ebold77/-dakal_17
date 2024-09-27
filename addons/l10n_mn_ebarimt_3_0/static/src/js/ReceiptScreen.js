odoo.define('l10n_mn_ebarimt_3_0.ReceiptScreen', function(require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const { useState } = owl;
    var rpc = require('web.rpc');

    const EBarimtReceiptScreen = ReceiptScreen => class extends ReceiptScreen {
        constructor() {
            super(...arguments);
        }
        mounted() {
                // Here, we send a task to the event loop that handles
                // the printing of the receipt when the component is mounted.
                // We are doing this because we want the receipt screen to be
                // displayed regardless of what happen to the handleAutoPrint
                // call.
                setTimeout(async () => {
                    // let images = this.orderReceipt.el.getElementsByTagName('img');
                    // for(let image of images) {
                    //     await image.decode();
                    // }
                    await this.handleAutoPrint();
                }, 0);
            }
        async handleAutoPrint() {
            const wait = (n) => new Promise((resolve) => setTimeout(resolve, n));
            if (this._shouldAutoPrint()) {
                await wait(3000);
                await this.printReceipt();
                if (this.currentOrder._printed && this._shouldCloseImmediately()) {
                    this.whenClosing();
                }
            }
        }
    }

    Registries.Component.extend(ReceiptScreen, EBarimtReceiptScreen);

    return ReceiptScreen;
});


