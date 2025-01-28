# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.addons.l10n_mn_report.models.report_helper import comma_me  # @UnresolvedImport
from odoo.addons.l10n_mn_web.models.time_helper import *


class ProductMoveCheckReport(models.AbstractModel):
    _name = 'report.l10n_mn_stock_report.product_move_check_report'
    _description = 'Report l10n_mn_stock_report Product Move Check Report'

    def get_heads(self, prod_id, warehouse_id):
        min_qty = max_qty = 0.0
        # Хамгийн бага нөөцийн дүрмээс pdf файлын толгой хэсгийн мэдээлэлд шаардлагатай өгөгдлүүдийг авч dictер буцааж байна
        self.env.cr.execute("""SELECT product_max_qty AS max_qty, product_min_qty AS min_qty
                        FROM stock_warehouse_orderpoint WHERE product_id = %s AND warehouse_id = %s""" % (prod_id, warehouse_id))
        point = self.env.cr.dictfetchall()
        # Хэрэв тухайн барааны хувьд дүрэм олдвол Дээд нөөц болон аюулгүй нөөц талбарууд утгатай болно
        if point and point[0]['max_qty']:
            max_qty = point[0]['max_qty']
        if point and point[0]['min_qty']:
            min_qty = point[0]['min_qty']
        product = self.env['product.product'].browse(prod_id)
        res = {'barcode': product.barcode or '',
               'name': product.name or '',
               'code': product.default_code or '',
               'uom': product.uom_id.name or '',
               'min_qty': min_qty,
               'max_qty': max_qty,
               'printed_date': str(get_day_like_display(fields.Datetime.now(), self.env.user))[:16]
        }
        return res

    def get_move_data(self, data, company, first_dict):
        # Бүртгэл хяналтын баримтын дэлгэц дээрх мэдээллүүдийг датанд хадгалсан байгаа
        res = []
        wiz = {'prod_id': data['wizard']['prod_id'],
               'from_date': data['wizard']['from_date'],
               'to_date': data['wizard']['to_date'],
               'warehouse_id': data['wizard']['warehouse_id'],
               'company_id': company,
               'report_type': data['wizard']['report_type'],
               'draft': data['wizard']['draft'],
               'lot_id': data['wizard']['prodlot_id'] and data['wizard']['prodlot_id'] or False}
        first_avail = first_dict['first_avail']
        first_price = first_dict['first_price']
        first_cost = first_dict['first_cost']
        # Барааны хөдөлгөөнөөс цуврал, байрлал, агуулахын нэр болон харилцагч, үнэ, төрөль тоо хэмжээ болон өртөг үнүүдийг result-д авна
        result = self.env['product.move.check.report.wizard'].get_move_data(wiz)
        total_dict = {'in_total': 0.0,
                      'out_total': 0.0,
                      'qty_total': 0.0,
                      'change_total': 0.0,
                      'last_cost': 0.0,
                      'first_avail': first_avail,
                      'first_total': (first_avail > 0 and first_price > 0 and first_avail * first_price) or 0.0,
                      'cost_total': (first_avail > 0 and first_cost > 0 and first_avail * first_cost) or 0.0,
                      'last_total': 0.0,
                      'last_avail': 0.0,
                      'first_price': first_price,
                      'first_cost': first_cost}
        in_total = out_total = 0.0
        change = change_total = 0.0
        last_cost = 0.0
        qty_total = 0.0
        if first_price != 0:
            change = first_price
        for r in result:
            Number = partner = seri = ''
            rep_type = ''
            in_qty = out_qty = 0
            if r['number']:
                if r['number'] == 'pos':
                    Number = r['location']
                else:
                    Number = r['number']
            if r['partner']:
                partner = r['partner']
            if r['rep_type']:
                if r['rep_type'] == 'purchase':
                    rep_type = u'Purchase'
                elif r['rep_type'] == 'inventory':
                    rep_type = u'Counting'
                elif r['rep_type'] == 'swap':
                    rep_type = u'Exchange'
                elif r['rep_type'] == 'consume':
                    rep_type = u'Domestic expenditure'
                elif r['rep_type'] == 'procure':
                    rep_type = u'Replenishment'
                elif r['rep_type'] == 'refund_purchase':
                    rep_type = u'Purchase refund'
                elif r['rep_type'] == 'refund':
                    rep_type = u'Return'
                elif r['rep_type'] == 'internal':
                    rep_type = u'Internal movement'
                elif r['rep_type'] == 'pos':
                    rep_type = u'Post sales'
                elif r['rep_type'] == 'mrp':
                    rep_type = u'Production'
                elif r['rep_type'] == 'refund_mrp':
                    rep_type = u'Production return'
                elif r['rep_type'] == 'price':
                    rep_type = u'Price changes'
                else:
                    rep_type = r['location']
            if r['rep_type'] in ('pos', 'internal') and r['partner'] is None:
                move = self.env['stock.move'].browse(r['move_id'])[0]
                partner = move.location_id.name
            if data['wizard']['report_type'] == 'owner':
                qty = 0.0
                if r['in_qty'] and r['in_qty'] != 0:
                    in_total += r['in_qty']
                    in_qty = r['in_qty']
                    first_avail += r['in_qty']
                    qty_total += r['in_qty']
                    qty = r['in_qty']
                if r['out_qty'] and r['out_qty'] != 0:
                    out_total += r['out_qty']
                    out_qty = r['out_qty']
                    first_avail -= r['out_qty']
                    qty_total += r['out_qty']
                    qty = r['out_qty']
                row = {'date': get_day_like_display(r['date'], self.env.user),
                       'rep_type': rep_type,
                       'number': '%s%s' % ('%s, ' % r['origin'] if 'origin' in r.keys() and r['origin'] else '', Number),
                       'change': change,
                       'seri': seri,
                       'partner': partner,
                       'state': r['state'],
                       'qty': comma_me(qty or 0.0),
                       'in_qty': comma_me(in_qty or 0.0),
                       'out_qty': comma_me(out_qty or 0.0),
                       'first_avail': comma_me(first_avail or 0.0)}
            elif data['wizard']['report_type'] == 'price':
                price = 0.0
                qty = 0.0
                unit = 0.0
                if r['in_qty'] and r['in_qty'] != 0:
                    in_qty = r['in_qty']
                    first_avail += r['in_qty']
                    qty = r['in_qty']
                    qty_total += r['in_qty']
                    if r['price']:
                        in_total += (in_qty * r['price'])
                if r['out_qty'] and r['out_qty'] != 0:
                    out_qty = r['out_qty']
                    first_avail -= r['out_qty']
                    qty = r['out_qty']
                    qty_total += r['out_qty']
                    if r['price']:
                        out_total += (out_qty * r['price'])
                if r['price']:
                    if change == 0:
                        change = r['price']
                    if change != r['price']:
                        if r['number'] and r['number'] == 'price':
                            unit = (r['price'] - change)
                            change_total += (unit * first_avail)
                    price = r['price']
                row = {'date': get_day_like_display(r['date'], self.env.user),
                       'rep_type': rep_type,
                       'number': '%s%s' % ('%s, ' % r['origin'] if 'origin' in r.keys() and r['origin'] else '', Number),
                       'change': change,
                       'seri': seri,
                       'partner': partner,
                       'state': r['state'],
                       'qty': comma_me(qty),
                       'price': comma_me(price),
                       'in_qty': comma_me((in_qty > 0 and price > 0 and in_qty * price) or 0.0),
                       'out_qty': comma_me((out_qty > 0 and price > 0 and out_qty * price) or 0.0),
                       'unit': comma_me((first_avail > 0 and unit > 0 and first_avail * unit) or 0.0),
                       'amount': comma_me((first_avail > 0 and price > 0 and first_avail * price) or 0.0),
                       'first_avail': comma_me(first_avail)}
            else:
                last_cost = first_cost
                cost = 0.0
                qty = 0.0
                costs = total_dict['cost_total']
                if r['in_qty'] and r['in_qty'] != 0:
                    qty = r['in_qty']
                    in_qty = r['in_qty']
                    qty_total += r['in_qty']
                    #last_cost = r['cost']
                    if r['cost']:
                        in_total += (in_qty * r['cost'])
                    if last_cost > 0 and first_avail > 0:
                        ftotal = last_cost * first_avail
                        mtotal = r['cost'] * r['in_qty']
                    else:
                        ftotal = 0
                        mtotal = r['cost'] * r['in_qty']
                    first_avail += r['in_qty']
                    if ftotal > 0 and mtotal > 0:
                        last_cost = (ftotal + mtotal) / first_avail
                if r['out_qty'] and r['out_qty'] != 0:
                    qty = r['out_qty']
                    out_qty = r['out_qty']
                    qty_total += r['out_qty']
                    first_avail -= r['out_qty']
                    #last_cost = r['cost']
                    if r['cost']:
                        out_total += (out_qty * r['cost'])
                if r['cost']:
                    cost = r['cost']
                costs += in_total
                costs -= out_total
                row = {'date': get_day_like_display(r['date'], self.env.user),
                       'rep_type': rep_type,
                       'number': '%s%s' % ('%s, ' % r['origin'] if 'origin' in r.keys() and r['origin'] else '', Number),
                       'change': change,
                       'seri': seri,
                       'partner': partner,
                       'state': r['state'],
                       'qty': comma_me(qty),
                       'cost': comma_me(cost),
                       'in_qty': comma_me((in_qty > 0 and cost > 0 and in_qty * cost) or 0.0),
                       'out_qty': comma_me((out_qty > 0 and cost > 0 and out_qty * cost) or 0.0),
                       'costs': comma_me((first_avail > 0 and cost > 0 and costs) or 0.0),
                       'first_avail': comma_me(first_avail)}
            res.append(row)
        total_dict['in_total'] = in_total
        total_dict['out_total'] = out_total
        total_dict['change_total'] = change_total
        total_dict['last_cost'] = last_cost
        total_dict['last_total'] = (first_avail > 0 and last_cost > 0 and first_avail * last_cost) or 0.0
        total_dict['last_avail'] = first_avail
        total_dict['qty_total'] = qty_total
        return res, total_dict

    @api.model
    def _get_report_values(self, ids, data=None):
        # pdf файл гаргалтанд шаардлагатай өгөгдлүүдийг цуглуулж байна
        report_obj = self.env['ir.actions.report']
        wizard_obj = self.env['product.move.check.report.wizard']
        report = report_obj._get_report_from_name('l10n_mn_stock_report.product_move_check_report')
        wizards = wizard_obj.browse(data['self'])

        from_date = data['wizard']['from_date']
        to_date = data['wizard']['to_date']
        prod_id = data['wizard']['prod_id']
        wname = data['wizard']['wname']
        warehouse_id = data['wizard']['warehouse_id']
        # Сонгосон агуулах болон барааны хувьд
        get_heads = self.get_heads(prod_id, warehouse_id)
        get_heads['lot'] = data['wizard']['lot_name']
        get_heads['expiration_date'] = data['wizard']['expiration_date']
        get_heads['warehouse'] = wname

        first_dict = {'first_avail': data['wizard']['first_avail'],
                      'first_cost': data['wizard']['first_cost'],
                      'first_price': data['wizard']['first_price']}
        lines, total = self.get_move_data(data, data['wizard']['company_id'], first_dict)
        total['in_total'] = comma_me(total['in_total'])
        total['out_total'] = comma_me(total['out_total'])
        total['change_total'] = comma_me(total['change_total'])
        total['last_cost'] = comma_me(total['last_cost'])
        total['last_total'] = comma_me(total['last_total'])
        total['last_avail'] = comma_me(total['last_avail'])
        total['qty_total'] = comma_me(total['qty_total'])
        total['first_total'] = comma_me(total['first_total'])
        total['cost_total'] = comma_me(total['cost_total'])
        total['first_avail'] = comma_me(total['first_avail'])
        total['first_price'] = comma_me(total['first_price'])
        total['first_cost'] = comma_me(total['first_cost'])
        return {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': wizards,
            'lines': lines,
            'total': total,
            'type': data['wizard']['report_type'],
            'from_date': from_date,
            'to_date': to_date,
            'company': data['wizard']['company'],
            'head': get_heads
        }
