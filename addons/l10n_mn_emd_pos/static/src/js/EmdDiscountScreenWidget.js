odoo.define('l10n_mn_health_insurance_pos_3_0.EmdDiscountScreenWidget', function(require) {
    'use strict';
	
	var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');

   	const PosComponent = require('point_of_sale.PosComponent');
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
    const { useState } = owl.hooks;

    class EmdDiscountScreenWidget extends ControlButtonsMixin(PosComponent) {
        constructor() {
            super(...arguments);
            useListener('click-create-discountorder', this._onClickCreateDiscountOrder);
			useListener('click-search-medicine', this._onClicSearchMedicine);
			// var register = $('#register-number-input');
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
			var pos_id = this.env.pos.config.id;
			var order = this.env.pos.get_order();
			var errorTimeout;
			var detail_list = [];
			var db = this.env.pos.db
			//self.clearFields();
			rpc.query({
                    model: 'pos.order', 
	                method: 'check_number', 
	                args: [regNumber, receiptNumber, pos_id],
                }).then(
				function (response) { // Success
					console.log('check number whole response', response);
					/*var jsonRes = {
					 		'cipherCode': "62026",
					 		'diagCodeUsed': "I10,I25,",
					 		'groupCode': null,
					 		'hosName': "ЭМДЕГ - ТЕСТ",
					 		'hosOfficeName': "Улаанбаатар",
					 		'hosSubOffName': "Багануур",
					 		'id': 752501315,
					 		'outDate': null,
					 		'patientFirstName': "МӨНХЖАРГАЛ",
					 		'patientLastName': "БАТБОЛД",
					 		'patientRegNo': "УШ99112103",
					 		'receiptDate': 1611648155000,
					 		'receiptDiag': "I10 Анхдагч даралт ихсэх өвчин;↵I25 Зүрхний архаг ишемит өвчин;↵",
					 		'receiptExpireDate': 1612252955000,
					 		'receiptNumber': 652811,
					 		'receiptPrintedDate': 1611648155000,
					 		'receiptType': 1,
					 		'receivedDate': null,
							'receivedHosId': null,
					 		'receivedHosName': null,
					 		'status': 1,
					 		'tbltCount': 2,
					 		'receiptDetails': [{
					 			'dailyCount': null,
					 			'dailyTimes': 2,
					 			'icdCode': "I10",
					 			'id': 1461638914,
					 			'isDiscount': 1,
					 			'oneTimeDose': 10,
					 			'packGroup': 218,
					 			'status': 0,
					 			'tbltDesc': "1ш өдөрт 2 уух",
					 			'tbltId': 4173,
					 			'tbltName': "lisinopril(10мг)",
					 			'tbltNameGroup': "45",
					 			'tbltSize': 56,
					 			'tbltType': null,
					 			'tbltTypeName': null,
					 			'totalDays': 28,
					 			}, 
					 			{
					 				'dailyCount': null,
					 				'dailyTimes': 1,
					 				'icdCode': "I25",
					 				'id': 1461638915,
					 				'isDiscount': 1,
									'oneTimeDose': 75,
					 				'packGroup': 151,
					 				'status': 0,
					 				'tbltDesc': "1ш өдөрт 1 уух",
					 				'tbltId': 4137,
					 				'tbltName': "clopidogrel(75мг)",
					 				'tbltNameGroup': "16",
					 				'tbltSize': 30,
					 				'tbltType': null,
					 				'tbltTypeName': null,
					 				'totalDays': 30
					 			}]
					 }*/
					if (response.error_message.length == 0) {
						var jsonRes = JSON.parse(response.json_data);
						order.accessToken = response.access_token;
						if (jsonRes === null) {
							$(".error-field").text("Эмийн бүртгэл олдсонгүй").height("1.2em");
							clearTimeout(errorTimeout);
							errorTimeout = setTimeout(function () {
								$(".error-field").height("0em");
							}, 4000);
						} else {
							var receiptType = "",
								status = "";
							switch (parseInt(jsonRes.result['receiptType'])) {
								case 1:
									receiptType = "Хөнгөлөлттэй жор";
									break;
								case 2:
									receiptType = "Канттай";
									break;
								case 3:
									receiptType = "13А";
									break;
								case 4:
									receiptType = "Үзлэг";
									break;
								case 5:
									receiptType = "Эмнэлэгийн хуудас";
									break;
							}
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
							$(".medicine-details-box .receiptType").text(receiptType);
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
								var product_list = db.get_product_by_emd_list(0);
								console.log('daatgaltai baraa==========', product_list)
								var options = '';
								for(var i = 0, len = product_list.length; i < len; i++){
									if (product_list[i]['insurance_list_id']){
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
								$(".discount-screen .top-content .next").removeClass("o_hide");
								alert("Жорд эм бичигдээгүй байна");
							}
						}
					} else { // ЭМД-ийн системтэй холбогдоогүй
						alert(response.error_message);
					}
				},
				function (error) { // Failed
					alert("[check number] Сервертэй холбогдоход алдаа гарлаа. " + error.message);
				}
				
				
			);
		}
		_onClickCreateDiscountOrder() {
			console.log('хөнгөлөлт олгох дарлаа', this);
			var self = this
			var db = this.env.pos.db
			var order = this.env.pos.get_order();
			var config = this.env.pos.config
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
			 		if (product.package_qty){
			 			qtyProd = qtyProd / product.package_qty;
			 		}
					dict['detailId']= detailId;
					dict['quantity']= qtyProd.toFixed(2);
				 	newOrderLine = order.add_product(product, dict);
				 	if (product.package_qty == 0){
				 		alert(product.display_name +"Барааны задгай тоо оруулаагүй байна.");
				 	}
			 	}
			 });
		
			
			var orders = order.get_orderlines(); //бүртгэсэн бараануудын жагсаалт
			order.pharmDiscount = Object.assign({
					lastName: $(".medicine-details-box .lastName").text(),
					firstName: $(".medicine-details-box .firstName").text(),
					register: $(".medicine-details-box .register").text(),
					receiptNumber: $(".medicine-details-box .receiptNumber").text(),
					receipt_id: $(".medicine-details-box .receipt_id").text(),
					
				}, self.pharmDiscount);
			order.ordersWithEmdDiscount = [];
			order.set_receiptNumber(order.pharmDiscount['receiptNumber']);	
			order.set_lastName(order.pharmDiscount['lastName']);	
			order.set_register(order.pharmDiscount['register']);	
			order.set_firstName(order.pharmDiscount['firstName']);	
			order.set_receipt_id(order.pharmDiscount['receipt_id']);	
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
				rpc.query({
                    model: 'pos.order', 
	                method: 'get_emd_discount', 
	                args: [JSON.stringify(orderData)],
                }).then(
					function (response) {
						if (orderElement.detail_id){
							var emd_discount = JSON.parse(response.emd_discount);
							var max_price = JSON.parse(response.max_price);
							console.log('max_price=============================', max_price, emd_discount)
							orderElement.set_emd_discount(emd_discount);
							orderElement.set_unit_price(max_price);
							orderElement.set_discount(emd_discount);
							if (emd_discount > 0) {
								order.ordersWithEmdDiscount.push(orderElement);
							}
						}
						ordersCount++;
						if (ordersLength == ordersCount) {
							self.showScreen('ProductScreen')
						}
					},
					function (error) {
						alert("[Get discount] Сервертэй холбогдоход алдаа гарлаа. Ахин оролдно уу!" + error.message);
					}
				);
			});
			
		
			
            this.showScreen('EmdDiscountScreenWidget');
        }
    }
	
	EmdDiscountScreenWidget.template = 'EmdDiscountScreenWidget';

    Registries.Component.add(EmdDiscountScreenWidget);


    return EmdDiscountScreenWidget;
});
