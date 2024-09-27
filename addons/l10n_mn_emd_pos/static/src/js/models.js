odoo.define('l10n_mn_health_insurance_pos_3_0.models', function (require) {
    "use strict";
	
	var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var utils = require('web.utils')
    var round_pr = utils.round_precision;
    var _super_posmodel = models.PosModel.prototype;
    var _super_order = models.Order.prototype;
    var _super_orderline = models.Orderline.prototype;

	var _t = core._t;
    var round_pr = utils.round_precision;

    models.load_fields("product.product", ["insurance_list_id", "package_qty"]);
    models.load_fields("res.company", ["ph_mobile"]);
    
	var _superOrder = models.Order;
    models.Order = models.Order.extend({
    	initialize: function(){
    		_super_order.initialize.apply(this, arguments);  
            this.emd_discount_amount = 0;
			this.receipt_number = 0;
			this.pharmDiscount = {}
        },
		set_receiptNumber: function (receiptNumber) {
	       	this.receipt_number = receiptNumber;
	        this.trigger('change',this);
	    },
		set_lastName: function (lastName) {
	       	this.last_name = lastName;
	        this.trigger('change',this);
	    },
		set_firstName: function (firstName) {
	       	this.first_name = firstName;
	        this.trigger('change',this);
	    },
		set_register: function (register) {
	       	this.register = register;
	        this.trigger('change',this);
	    },
		set_receipt_id: function (receipt_id) {
	       	this.receipt_id = receipt_id;
	        this.trigger('change',this);
	    },
        add_product: function(product, options){
            if(this._printed){
                this.destroy();
                return this.pos.get_order().add_product(product, options);
            }
            this.assert_editable();
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;
            var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});
            if(options.quantity !== undefined){
                line.set_quantity(options.quantity);
            }
            if(options.detailId !== undefined){
                line.set_detail_id(options.detailId);
            }
            console.log('options.price---->>', options.price)
            if(options.price !== undefined){
                line.set_unit_price(options.price);
            }

            //To substract from the unit price the included taxes mapped by the fiscal position
            this.fix_tax_included_price(line);

            if(options.discount !== undefined){
                line.set_discount(options.discount);
            }

            if(options.extras !== undefined){
                for (var prop in options.extras) {
                    line[prop] = options.extras[prop];
                }
            }

            var last_orderline = this.get_last_orderline();
            if( last_orderline && last_orderline.can_be_merged_with(line) && options.merge !== false){
                last_orderline.merge(line);
            }else{
                this.orderlines.add(line);
            }
            this.select_orderline(this.get_last_orderline());

            if(line.has_product_lot){
            // START: Disabling popup of product on initiate
            //    this.display_lot_popup();
            // END
            }
        },
        get_total_emd_discount_amount: function(){
        	var emd_discount_amount = 0;
            var lines = this.get_orderlines();
            if (lines){
            	for (var i = 0; i < lines.length; i++) {
            		emd_discount_amount += (lines[i].get_emd_discount_amount() * lines[i].get_quantity());
                }
            }
            return emd_discount_amount;
        },
        get_total_with_tax_without_emd_discount: function() {
	        return this.get_total_without_tax() + this.get_total_tax() - this.get_total_emd_discount_amount();
	    },
		
		 export_as_JSON: function() {
            var result = _superOrder.prototype.export_as_JSON.apply(this,arguments);
            result.receipt_number = this.receipt_number;
			result.last_name = this.last_name;
			result.first_name = this.first_name;
			result.register = this.register;
			result.receipt_id = this.receipt_id;
            return result;
        },

        export_for_printing: function() {
            var receipt = _superOrder.prototype.export_for_printing.apply(this,arguments);
            receipt.company.ph_mobile = this.pos.company.ph_mobile;
            
            return receipt;
        },
	
    });
    
    models.Orderline = models.Orderline.extend({
    	initialize: function(){
    		_super_orderline.initialize.apply(this, arguments);  
            this.emd_discount = 0;
            this.emd_discount_str = '0';
            this.emd_discount_qty = 0;
        },
        set_quantity: function (quantity) {
            this.order.assert_editable();
            if (quantity === 'remove') {
                this.order.remove_orderline(this);
                return;
            } else {
                var quant = parseFloat(quantity) || 0;
                this.quantity = round_pr(quant, 0.00000001);
                this.quantityStr = '' + this.quantity;
            }
            this.trigger('change', this);
        },
        set_detail_id: function (detail_id) {
        	this.order.assert_editable();
	       	this.detail_id = detail_id;
	        this.trigger('change',this);
	    },
	    // sets a emd discount [0,100]%
	    set_emd_discount: function(discount){
	        var disc = Math.min(Math.max(parseFloat(discount) ||  0, 0),100);
	        this.emd_discount = disc;
	        this.emd_discount_str = '' + disc;
	        this.trigger('change', this);
	    },
	    // returns the emd discount [0,100]%
	    get_emd_discount: function(){
	        return this.emd_discount || 0;
	    },
	    get_emd_discount_str: function(){
	        return this.emd_discount_str || '';
	    },
		get_unit_price_after_discount: function(){
        	return this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        },
        
	    // returns the emd discount amount from discount percent
	    get_emd_discount_amount: function(){
	    	if (this.get_emd_discount() != 0){
                print('this.get_unit_price_after_discount() * (this.get_emd_discount() / 100.0)====', this.get_unit_price_after_discount() * (this.get_emd_discount() / 100.0))
	    		return this.get_unit_price_after_discount() * (this.get_emd_discount() / 100.0);
	    	}else{
	    		return 0;
	    	}
	    },

        get_full_product_name: function () {
            if (this.full_product_name) {
                return this.full_product_name
            }
            var full_name = '['+ this.product.default_code + '] '+ this.product.display_name;
            if (this.description) {
                full_name += ` (${this.description})`;
            }
            return full_name;
        },

        export_as_JSON: function() {
            var result = _super_orderline.export_as_JSON.call(this);
            result['emd_discount'] = this.get_emd_discount();
			result['detail_id'] = this.detail_id;
            return result;
        },

		
		
    });

    return {
		Orderline: models.Orderline,
		Order: models.Order,
		PosModel: models.PosModel,
	};

});