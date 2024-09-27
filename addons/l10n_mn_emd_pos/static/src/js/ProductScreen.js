odoo.define('l10n_mn_health_insurance_pos_3_0.ProductScreen', function(require) {
    'use strict';

   	const ProductScreen = require('point_of_sale.ProductScreen');
	const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    const EmdProductScreen = ProductScreen => class extends  ProductScreen {
        constructor() {
            super(...arguments);
            useListener('click-discount-emd', this._onClickDiscountPharm);
        }
        
		_onClickDiscountPharm() {
            console.log('dsfdsfdsf');
            this.showScreen('EmdDiscountScreenWidget');
        }
    }
	
	Registries.Component.extend(ProductScreen, EmdProductScreen);

    return ProductScreen;
});
