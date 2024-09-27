odoo.define('l10n_mn_ebarimt_3_0.ProductScreen', function(require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const EBarimtProductScreen = ProductScreen => class extends ProductScreen {
        async _clickProduct(event) {
            let last_order_line = this.currentOrder.get_last_orderline();
            let callParent = true;
            const product = event.detail;
            if (!product.default_code) {
                callParent = false;
                await this.showPopup('ErrorPopup',{
                    title: this.env._t("No ''Internal Reference''"),
                    body:  this.env._t("Please register ''Internal Reference'' of this product.")
                });
            }

            if (!product.ebarimt_gs1barcode_id) {
                callParent = false;
                await this.showPopup('ErrorPopup',{
                    title: this.env._t("No ''Classification Code''"),
                    body:  this.env._t("Please register ''Classification Code'' of this product.")
                });
            }

            if (!product.taxes_id) {
                callParent = false;
                await this.showPopup('ErrorPopup',{
                    title: this.env._t("Product has no tax"),
                    body:  this.env._t("Please register product tax according to Mongolian Tax Law.")
                });
            }

            if (callParent) {
                super._clickProduct(event);
            }
        }
    };

    Registries.Component.extend(ProductScreen, EBarimtProductScreen);

    return ProductScreen;
});
