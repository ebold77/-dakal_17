odoo.define('l10n_mn_ebarimt_3_0.Chrome', function(require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');

    const EBarimtChrome = Chrome => class extends Chrome {
        async _closePos() {
            super._closePos();
        }
    }

    Registries.Component.extend(Chrome, EBarimtChrome);

    return Chrome;
});