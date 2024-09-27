odoo.define('l10n_mn_ebarimt_3_0.ClientDetailsEdit', function(require) {
    'use strict';

    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    const EBarimtClientDetailsEdit = ClientDetailsEdit => class extends ClientDetailsEdit {
        constructor() {
            super(...arguments);
        }

        async getPartnerInformation() {
            if (this.changes.vat) {
                let result = await this.rpc({
                                          model: 'pos.config', 
                                          method: 'get_partner_info', 
                                          args: [this.changes.vat],
                             });
                this.changes.name = result['name'];
                this.props.partner.name = this.changes.name;
                this.render();
            }
        }

        changeCompanyType(event) {
            this.changes.company_type = event.target.value;
        }
    }

    Registries.Component.extend(ClientDetailsEdit, EBarimtClientDetailsEdit);

    return ClientDetailsEdit;
});