odoo.define('l10n_mn_hr_attendance.BasicView', function (require) {
    "use strict";

    var session = require('web.session');
    var BasicView = require('web.BasicView');

    BasicView.include({
        init: function(viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            var model = self.controllerParams.modelName;

//          ХН менежер эрхтэй хүнд л ирцийг архивлах, архиваас гаргах товч харагдана.
            if(model == 'hr.attendance') {
                session.user_has_group('hr.group_hr_manager').then(function(has_group) {
                    if(!has_group) {
                        self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                    }
                });
            }
        },
    });
});