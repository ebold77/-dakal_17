# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class res_company(models.Model):
    _inherit = "res.company"

    sale_template = fields.Selection([
            ('mn_standard', 'Mongolian Standart'),
            ('odoo_standard', 'Odoo Standard'),
        ], 'Sale')
    purchase_template = fields.Selection([
           ('mn_standard', 'Mongolian Standart'),
            ('odoo_standard', 'Odoo Standard'),
        ], 'Purchase')
    stock_template = fields.Selection([
            ('mn_standard', 'Mongolian Standart'),
            ('odoo_standard', 'Odoo Standard'),
        ], 'Stock')
    account_template = fields.Selection([
            ('mn_standard', 'Mongolian Standart'),
            ('odoo_standard', 'Odoo Standard'),
        ], 'Account')


class account_invoice(models.Model):
    _inherit = "account.move"
 
#     paypal_chk = fields.Boolean("Paypal")
#     paypal_id = fields.Char("Paypal Id")


    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env.ref('l10n_mn_professional_reports_templates.custom_account_invoices').report_action(self)
    


class res_company(models.Model):
    _inherit = "res.company"

    bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account')

class res_partner_bank(models.Model):
    _inherit = "res.partner.bank"

    view_report = fields.Boolean('Show in the Invoice')


class sale_order(models.Model):
    _inherit = 'sale.order'


    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref('l10n_mn_professional_reports_templates.custom_report_sale_order').report_action(self)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env.ref('l10n_mn_professional_reports_templates.custom_report_purchase_quotation').report_action(self)


class StockPicking(models.Model):
    _inherit = "stock.picking"
# 
#     def do_print_picking(self):
#         self.write({'printed': True})
#         return self.env.ref('l10n_mn_professional_reports_templates.custom_report_deliveryslip').report_action(self)