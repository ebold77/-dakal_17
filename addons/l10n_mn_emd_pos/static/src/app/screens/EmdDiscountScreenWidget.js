/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";
import { useErrorHandlers, useAsyncLockedMethod } from "@point_of_sale/app/utils/hooks";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { DatePickerPopup } from "@point_of_sale/app/utils/date_picker_popup/date_picker_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ConnectionLostError } from "@web/core/network/rpc_service";

import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState, onMounted } from "@odoo/owl";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { floatIsZero, roundPrecision as round_pr } from "@web/core/utils/numbers";
import { sprintf } from "@web/core/utils/strings";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

export class EmdDiscountScreenWidget extends Component {
	static template = "EmdDiscountScreenWidget";
    static components = {

    };

    setup() {
        this.pos = usePos();
        this.ui = useState(useService("ui"));
        this.orm = useService("orm");
        this.popup = useService("popup");
    
    }


	changeRegister(event) {
		var register = $('#reg_no');
		register.keyup(function (e) {
			console.log('e.keyCode', e.keyCode)
			if (e.keyCode === 13) {
				$(".discount-screen .search-medicine").click();		
				}
			});	
	}
	_onClicSearchMedicine(){
		var receiptNumber = $(".receipt-number-input").val();
		var regNumber = $(".register-number-input").val();
		console.log('this.env.pos============',this.pos)
		var pos_id = this.pos.config.id;
		var order = this.pos.get_order();
		var errorTimeout;
		var detail_list = [];
		var db = this.pos.db
		//self.clearFields();
		const receipt_data = this.orm.call("pos.order", "check_number", [
			regNumber, receiptNumber, pos_id
				]);
		
		receipt_data.then((response) => {
				console.log(response.json_data);
				var jsonRes = JSON.parse(response.json_data);
				console.log('jsonRes=============', jsonRes)
				var status = "";		
				switch (parseInt(jsonRes.result['status'])) {
					case 0:
						status = "Идэвхигүй";
						break;
					case 1:
						status = "Идэвхитэй";
						break;
					case 2:
						status = "Энгийн жор";
						break;
					case 3:
						status = "Худалдаж авсан";
						break;
					case 4:
						status = "Хянасан";
						break;
					case 5:
						status = "Хугацаа дууссан";
						break;
				}
				var receiptExpireDate = new Date(jsonRes.result['receiptExpireDate']);
				var expireDate = receiptExpireDate.getFullYear() + "-" + (receiptExpireDate.getMonth() + 1) + "-" + receiptExpireDate.getDate();
				var receiptPrintedDate = new Date(jsonRes.result['receiptDate']);
				var printedDate = receiptPrintedDate.getFullYear() + "-" + (receiptPrintedDate.getMonth() + 1) + "-" + receiptPrintedDate.getDate();
				var receiptDiag = !!jsonRes.result['receiptDiag'] ? jsonRes.result['receiptDiag'] : "";
			
				$(".medicine-details-box .lastName").text(jsonRes.result['patientLastName']);
				$(".medicine-details-box .firstName").text(jsonRes.result['patientFirstName']);
				$(".medicine-details-box .register").text(jsonRes.result['patientRegNo']);
				$(".medicine-details-box .receiptNumber").text(jsonRes.result['receiptNumber']);
				$(".medicine-details-box .prescriptionType").text(jsonRes.result['prescriptionType']);
				$(".medicine-details-box .prescriptionTypeName").text(jsonRes.result['prescriptionTypeName']);
				$(".medicine-details-box .receiptDiag").text(receiptDiag);
				$(".medicine-details-box .receiptExpireDate").text(expireDate);
				$(".medicine-details-box .receiptPrintedDate").text(printedDate);
				$(".medicine-details-box .status").text(status);
				$(".medicine-details-box .hosOfficeName").text(jsonRes.result['hosOfficeName']);
				$(".medicine-details-box .hosSubOffName").text(jsonRes.result['hosSubOffName']);
				$(".medicine-details-box .hosName").text(jsonRes.result['hosName']);
				$(".medicine-details-box .cipherCode").text(jsonRes.result['cipherCode']);
				$(".medicine-details-box .tbltCount").text(jsonRes.result['tbltCount']);
				$(".medicine-details-box .receipt_id").text(jsonRes.result['id']);
				var receiptDetails = jsonRes.result['receiptDetails'];
				console.log('receiptDetails=====', receiptDetails)
				if(receiptDetails.length > 0){
					for (var i = 0; i < receiptDetails.length; i++) {
						var receiptDetail = receiptDetails[i];	
						detail_list.push(receiptDetail)
						var tbltTypeName = !!receiptDetail.tbltTypeName ? receiptDetail.tbltTypeName : "";
						$(".medicine-list .medicine-list-contents").append(
							"<tr class='medicine-line'>" +
							"<td id='detailId'>" + receiptDetail.id + "</td>" +
							"<td>" + receiptDetail.tbltName + "</td>" +
							"<td id='tbltSize'>" + receiptDetail.packGroup + "</td>" +
							"<td id='tbltSize'>" + receiptDetail.tbltSize + "</td>" +
							"<td>" + receiptDetail.totalDays + "</td>" +
							"<td>" + receiptDetail.tbltDesc + "</td>" +
							"<td>" + (parseInt(receiptDetail.status) == 1 ? "Борлуулсан" : "Борлуулаагүй") + "</td>" +
							"<td id='prodId'>" +
									" <input list='screens.screenid-datalist' id='input-id' type='text' \
										class='description form-control' onblur='self.on_create_line'>" +
									" <datalist id='screens.screenid-datalist'> " +
								"</datalist>" + 
								"</input> " +
								"</td>" +
							"</tr>");
						
					}
				
					// Даатгалын хөнгөлөлттэй эмээр input datalist цэнэглэх
					var product_list = [];
					console.log('prescriptionType===>>',parseInt(jsonRes.result['prescriptionType']))
					if(parseInt(jsonRes.result['prescriptionType']) ==1){
						product_list = db.get_product_by_emd_list(0);
					}
					else{
						// Энгийн жороор олгох бараагаар input datalist цэнэглэх
						product_list = db.get_product_by_all(0)
					}
					
					var options = '';
					for(var i = 0, len = product_list.length; i < len; i++){
					
						if (product_list[i]['emd_insurance_list_id']){
							options += '<option value="'+product_list[i]['id']+ '-'+product_list[i]['display_name']+ '" />';
							}
						}
					document.getElementById('screens.screenid-datalist').innerHTML = options;
					self.pharmDiscount = jsonRes;
					if (parseInt(jsonRes.status) == 1 || parseInt(jsonRes.status) == 3){
						$(".discount-screen .top-content .next").removeClass("o_hide");
					}
				}
				else { // ЭМД-ийн системтэй холбогдоогүй
					// $(".discount-screen .top-content .next").removeClass("o_hide");
					alert("Жорд эм бичигдээгүй байна");
				}
			});
	}
	
	_onClickCreateDiscountOrder() {
		console.log('хөнгөлөлт олгох дарлаа', this);
		var self = this
		var db = this.pos.db
		var order = this.pos.get_order();
		var config = this.pos.config
		//Хөнгөлөлттэй пос ордер үүсгэх
		$('#medicine-table tr').each(function() {
			 var detailId = $(this).find("td:eq(0)").html();    
			 var qtyProd = $(this).find("td:eq(3)").text();
			 var prod = $(this).find("td:eq(7) input[type='text']").val();
			 var newOrderLine;
			console.log('prod============', prod, qtyProd, detailId )
			 if (prod){
				 var prodId = prod.split('-')
				 var product = db.get_product_by_id(prodId[0])
				 
				var dict = []; // create an empty array
				
				 // ЭМД-н хөнгөлөлт үзүүлсэн бол тухайн барааны default тоог буцаахдаа
				 // барааны задгай тоо хэмжээг тооцож буцаадаг болгов.
				if (product.package_qty == 0){
					 alert(product.display_name +"Барааны задгай тоо оруулаагүй байна.");
				 }
				 if (product.package_qty){
					 qtyProd = qtyProd / product.package_qty;
				 }
				dict['detailId']= detailId;
				dict['quantity']= qtyProd;
				newOrderLine = order.add_product(product, dict);
				 
			 }
		 });
	
		
		var orders = order.get_orderlines(); //бүртгэсэн бараануудын жагсаалт
		order.pharmDiscount = Object.assign({
				lastName: $(".medicine-details-box .lastName").text(),
				firstName: $(".medicine-details-box .firstName").text(),
				register: $(".medicine-details-box .register").text(),
				receiptNumber: $(".medicine-details-box .receiptNumber").text(),
				receipt_id: $(".medicine-details-box .receipt_id").text(),
				prescriptionType: $(".medicine-details-box .prescriptionType").text()
			}, self.pharmDiscount);
		order.ordersWithEmdDiscount = [];
		order.set_receiptNumber(order.pharmDiscount['receiptNumber']);	
		order.set_lastName(order.pharmDiscount['lastName']);	
		order.set_register(order.pharmDiscount['register']);	
		order.set_firstName(order.pharmDiscount['firstName']);	
		order.set_receipt_id(order.pharmDiscount['receipt_id']);
		order.set_prescriptionType(parseInt(order.pharmDiscount['prescriptionType']))	
		var ordersLength = orders.length;
		var ordersCount = 0;
		orders.forEach(function (orderElement) {
			console.log('orderElement.price', orderElement.price, orderElement.quantity)
			var orderData = {
				"pricelist_id": config.emd_price_list_id[0],
				"price": orderElement.price,
				"quantity": orderElement.quantity,
				"productId": orderElement.product.id
			}; // get_discount луу явуулах дата (JSON)
			console.log('order.pharmDiscount[\'prescriptionType\']', order.prescriptionType)
			if (order.pharmDiscount['prescriptionType']==1){
				console.log('self=========', self)
				const emd_data =  self.orm.call("pos.order", "get_emd_discount", [
					JSON.stringify(orderData)
						]);
				
				emd_data.then((response) => {
					console.log(response.json_data);
					if (orderElement.detail_id){
						var emd_discount = JSON.parse(response.emd_discount);
						var max_price = JSON.parse(response.max_price);
						var qty = JSON.parse(response.qty);
						console.log('max_price=============================',response, max_price, emd_discount)
						orderElement.set_emd_discount(emd_discount);
						orderElement.set_unit_price(max_price);
						orderElement.set_discount(emd_discount);
						orderElement.set_quantity(qty);
						if (emd_discount > 0) {
							order.ordersWithEmdDiscount.push(orderElement);
						}
					}
					ordersCount++;
					if (ordersLength == ordersCount) {
						self.pos.showScreen('ProductScreen')
					}

				});
			}
			else{
				self.pos.showScreen('ProductScreen')
			}

		});
		
	
		
		self.pos.showScreen('EmdDiscountScreenWidget');
	}
}

registry.category("pos_screens").add("EmdDiscountScreenWidget", EmdDiscountScreenWidget);