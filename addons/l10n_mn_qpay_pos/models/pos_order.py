# -*- coding: utf-8 -*-

import json
import logging
import requests
import time
from datetime import date, datetime
from time import mktime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        # self.get_qpay_token()
        self.create_invoice_qpay()

    def get_qpay_token(self):

        url = "https://merchant-sandbox.qpay.mn/v2/auth/token"
        payload = ""
        headers = {
                    'Authorization': 'Basic'
        }
        access_token = ''
        response = requests.request("POST", url, headers=headers, data=payload)
        print('response.text----------->>', response.text)

        if response.status_code == 200:
            new_data = json.loads(response.text)
            access_token = new_data['access_token']
        else:
            error_message = u'QPay-ийн системтэй холбогдоход алдаа гарлаа'
            _logger.error(u'Аccess token авахад алдаа гарлаа. %s', response.text)
        print('access_token============', access_token)
        return  access_token
        
    def refresh_qpay_token(self):

        url = "https://merchant-sandbox.qpay.mn/v2/auth/refresh"

        payload = {}
        headers = {
                    'Authorization': 'Bearer'
        }
        access_token = ''
        response = requests.request("POST", url, headers=headers, data=payload)
        print('response.text----------->>', response.text)

        if response.status_code == 200:
            new_data = json.loads(response.text)
            access_token = new_data['access_token']
        else:
            error_message = u'QPay-ийн системтэй холбогдоход алдаа гарлаа'
            _logger.error(u'Аccess token авахад алдаа гарлаа. %s', response.text)
        print('access_token============', access_token)
        return  access_token

    def create_invoice_qpay(self):
        new_data = []
        url = "https://merchant-sandbox.qpay.mn/v2/invoice"

        payload = json.dumps({
        "invoice_code": "TEST_INVOICE",
        "sender_invoice_no": "9329873948",
        "sender_branch_code": "branch",
        "invoice_receiver_code": "terminal",
        "invoice_receiver_data": {
            "register": "TA89102712",
            "name": "Бат",
            "email": "info@info.mn",
            "phone": "99887766"
        },
        "invoice_description": "Invoice description",
        "invoice_due_date": None,
        "allow_partial": False,
        "minimum_amount": None,
        "allow_exceed": False,
        "maximum_amount": None,
        "note": None,
        "lines": [
            {
                "tax_product_code": None,
                "line_description": "Invoice description",
                "line_quantity": "1.00",
                "line_unit_price": "10000.00",
                "note": "",
                "discounts": [
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ],
                "surcharges": [
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ],
                "taxes": [
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ]
            },
            {
                "tax_product_code": None,
                "line_description": "Invoice description",
                "line_quantity": "1.00",
                "line_unit_price": "10000.00",
                "note": "",
                "discounts": [
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ],
                "surcharges": [
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ],
                "taxes": [
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ]
            },
            {
                "tax_product_code": None,
                "line_description": "Invoice description",
                "line_quantity": "1.00",
                "line_unit_price": "10000.00",
                "note": "",
                "discounts": [
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "discount_code": "NONE",
                    "description": "uPoint хямдрал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ],
                "surcharges": [
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "surcharge_code": "NONE",
                    "description": "Хүргэлтийн зардал",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ],
                "taxes": [
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    },
                    {
                    "tax_code": "VAT",
                    "description": "НӨАТ",
                    "amount": 100,
                    "note": "тэмдэглэл"
                    }
                ]
            }
        ]
        })
        headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            new_data = json.loads(response.text)

        return new_data
    
    ########################### Төлбөрийн нэхэмжлэл цуцлах ########################
    def cancel_invoice_qpay(self):
        new_data = []
        url = "https://merchant-sandbox.qpay.mn/v2/invoice/"
        
        payload = {
            'invoice_id': "071f45e6-b6e6-4562-a470-8457269d251a"
        }

        headers = {
            'Authorization': 'Bearer'
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)
        print(response.text)
        if response.status_code == 200:
            new_data = json.loads(response.text)

        return new_data

    ########################### Төлбөрийн мэдээлэл авах ########################
    def get_payment_qpay(self):
        new_data = []
        url = "https://merchant-sandbox.qpay.mn/v2/payment/"
        
        payload = {}

        headers = {
            'Authorization': 'Bearer'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        print(response.text)
        if response.status_code == 200:
            new_data = json.loads(response.text)

        return new_data

    ########################### Төлбөр төлөгдсөн эсэхийг шалгах ########################
    def check_payment_qpay(self):
        new_data = []
        url = "https://merchant-sandbox.qpay.mn/v2/payment/check"
        
        payload = json.dumps({
            "object_type": "INVOICE",
            "object_id": "071f45e6-b6e6-4562-a470-8457269d251a",
            "offset": {
                "page_number": 1,
                "page_limit": 100
            }
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)
        if response.status_code == 200:
            new_data = json.loads(response.text)

        return new_data
     ########################## Төлөгдсөн төлбөр цуцлах #####################################
    def cancel_payment_qpay(self):
        new_data = []
        url = "https://merchant-sandbox.qpay.mn/v2/payment/cancel/"
        
        payload = "{\n    \"callback_url\":\"https://qpay.mn/payment/result?payment_id=ccb8e022-0187-4184-bd3f-a6d9ce231e6f\",\n    \"note\":\"butsaalt\"\n}"

        headers = {
            'Authorization': 'Bearer'
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)
        print(response.text)
        if response.status_code == 200:
            new_data = json.loads(response.text)

        return new_data
    ########################## Төлбөр буцаах #####################################
    def refund_payment_qpay(self):
        new_data = []
        url = "https://merchant-sandbox.qpay.mn/v2/payment/refund/"
        
        payload = "{\n    \"callback_url\":\"https://qpay.mn/payment/result?payment_id=ccb8e022-0187-4184-bd3f-a6d9ce231e6f\",\n    \"note\":\"butsaalt\"\n}"

        headers = {
            'Authorization': 'Bearer'
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)
        print(response.text)
        if response.status_code == 200:
            new_data = json.loads(response.text)

        return new_data