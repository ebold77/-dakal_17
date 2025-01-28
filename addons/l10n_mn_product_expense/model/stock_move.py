# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = "stock.move"

    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            # ############ BEGIN CHANGE ##########################
            # Бараа материалын шаардахаас үүсэх журналын бичилтын КТ данс нь шаардахын мөрийн дансаар үүсдэг болгосон
            if hasattr(self.picking_id, 'expense_id') and self.picking_id.expense_id:
                account_id = False
                for line in self.picking_id.expense_id.expense_line_ids:
                    if line.product_id.id == self.product_id.id:
                        account_id = line.account_id.id
                acc_src = account_id
            # ############ END CHANGE ############################
            if location_from and location_from.usage == 'customer':  # goods returned from customer
                self.with_company(company_to)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty,
                                                                        description, svl_id, cost)
            else:
                self.with_company(company_to)._create_account_move_line(acc_src, acc_valuation, journal_id, qty,
                                                                        description, svl_id, cost)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = -1 * cost
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            # ############ BEGIN CHANGE ##########################
            # Бараа материалын шаардахаас үүсэх журналын бичилтын ДТ данс нь шаардахын мөрийн дансаар үүсдэг болгосон

            if hasattr(self.picking_id, 'expense_id') and self.picking_id.expense_id:
                account_id = False
                for line in self.picking_id.expense_id.expense_line_ids:
                    if line.product_id.id == self.product_id.id:
                        account_id = line.account_id.id
                acc_dest = account_id
            # ############ END CHANGE ############################
            if location_to and location_to.usage == 'supplier':  # goods returned to supplier
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_src, journal_id, qty,
                                                                          description, svl_id, cost)
            else:
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty,
                                                                          description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if self._is_dropshipped():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_src, acc_valuation, journal_id, qty,
                                                                                 description, svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty,
                                                                                 description, svl_id, cost)
            elif self._is_dropshipped_returned():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_src, journal_id, qty,
                                                                                 description, svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty,
                                                                                 description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            self._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=self.product_id)

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        """ Overridden from stock_account to support amount_currency on valuation lines generated from po
        """
        self.ensure_one()
        inventory_id = False
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                     debit_account_id, credit_account_id, description)
        # Хэрвээ Барааны шаардахаас үүссэн ажил гүйлгээний мөр бол шинжилгээний дансыг онооно.
        if self.picking_id and self.picking_id.expense_id:
            analytic_account_id = False
            for line in self.picking_id.expense_id.expense_line_ids:
                if line.product_id.id == self.product_id.id:
                    analytic_account_id = line.analytic_account_id.id
                if self._is_out():
                    rslt['debit_line_vals']['analytic_account_id'] = analytic_account_id
                else:
                    rslt['credit_line_vals']['analytic_account_id'] = analytic_account_id
        return rslt