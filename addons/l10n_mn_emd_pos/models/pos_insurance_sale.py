# -*- coding: utf-8 -*-
# import json
import logging
import requests
from datetime import datetime
from time import mktime
import simplejson as json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError  # @UnresolvedImport

_logger = logging.getLogger(__name__)


class PosInsuranceSale(models.Model):
    _name = "pos.insurance.sale"
    _order = "date desc, id desc"
    _description = "POS sale order Health Insurance"

    name = fields.Char('Reciept Number', required=True)
    date = fields.Datetime('Date')
    totalAmt = fields.Float('Total Amount')
    insAmt = fields.Float('Insurance Amount')
    vatAmt = fields.Float('Vat Amount')
    netAmt = fields.Float('Net Amount')
    lastName = fields.Char('Last Name')
    firstName = fields.Char('First Name')
    register = fields.Char('Register Number', required=True)
    detCnt =  fields.Integer('detCnt')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sented', 'Sented')], default="draft")
    insurance_line = fields.One2many('pos.insurance.sale.line', 'parent_id', 'Line')
    origin = fields.Many2one('pos.order', string='Origin')
    partner_id = fields.Many2one('res.partner', string='Partner')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    ddtd = fields.Char('Unique Number')
    config_id = fields.Many2one('pos.config', string='POS Configure', required=True)
    receipt_id = fields.Integer('Receipt ID')
    
    def action_draft(self):
        self.write({
                  'state':'draft'
                  })

    # Уг функц нь Жорын дугаар, регистрийн дугаар, ПОС-н тохиргоо 
    # гэсэн заавал бөглөх 3 талбар авч "Жорын дугаараар татах" 
    # товч дарах үед ЭМД-н системээс ирэх утгуудыг дэлгэцэнд оруулна.
    def get_data(self):
        pos_order_obj = self.env['pos.order']
        data_dict = False
        for obj in self:
            data_dict = pos_order_obj.check_number(obj.register, obj.name, obj.config_id.id)
            if data_dict:    
                data = json.loads(data_dict['json_data'])
                if data:
                    obj.receipt_id = data['id']
                    obj.lastName = data['patientLastName']
                    obj.firstName = data['patientFirstName']
                    obj.date = datetime.now()
                    receipt_detail = data['receiptDetails']
                    obj.insurance_line.unlink()  # дахин дарагдах үед ажиллана.
                    line_obj = self.env['pos.insurance.sale.line']
                    vals = []
                    for line in receipt_detail:
                        vals.append({
                            'intern_name':line['tbltName'],
                            'parent_id':obj.id,
                            'product_id':False,
                            'detail_id':line['id']
                        })
                    if vals:
                        for line in vals:
                            line_obj.create(line)
                else:
                    raise UserError(u'Алдаатай бичилт оруулсан эсвэл жорын хугацаа дууссан байна!')
            else:
                raise UserError(u'Алдаатай бичилт оруулсан эсвэл жорын хугацаа дууссан байна!')

    def send_emd_cron(self):
        draft_insurances = self.search([('state', '=', 'draft')])
        if draft_insurances:
            for pos_insurance_id in draft_insurances:
                _logger.info(u' %s дугаартай жорыг автомат крон функц илгээж байна. ' % pos_insurance_id.name)
                check_number = pos_insurance_id.name
                recipt_data = {}
                json_data = []
                access_token = ''
                error_message = ''
                head = {'Authorization': 'Basic VV9mZl05Qmp5WlhMbUcmZHcmOlo3JHtFenlyRDRheUN9RkxkJg=='}
                data = {
                    'grant_type': 'password',
                    'username': pos_insurance_id.config_id.user_name,
                    'password': pos_insurance_id.config_id.password,
                }
                emd_url = 'https://ws.emd.gov.mn/oauth/token?'
                response = requests.post(emd_url, params=data, headers=head, verify=False)
                if response.status_code == 200:
                    new_data = json.loads(response.text)
                    access_token = new_data['access_token']
                    regNumber = pos_insurance_id.register
                    _logger.info(u' %s дугаартай жороор ЭМД-н системээс авсан токен %s' % (pos_insurance_id.name, access_token))
                    recipt_data = self.env['pos.insurance.send'].check_reciept(access_token, regNumber, check_number)
                    if not recipt_data:
                        _logger.warn(u' %s дугаартай жороор ЭМД-н системээс авсан токеноор илгээх боломжгүй!!!' % pos_insurance_id.name)
                    json_data = json.dumps(recipt_data)
                    self.env['pos.insurance.send'].send_emd(pos_insurance_id.id, access_token, pos_insurance_id.config_id.id)
                else: 
                    error_message = u'ЭМД-ийн системтэй холбогдоход алдаа гарлаа'
                    _logger.error(u'Аccess token авахад алдаа гарлаа.')
                    raise ValidationError(u'%s дугаартай жор ЭМД системтэй холбогдож чадсангүй! ' % pos_insurance_id.name)

    def get_token(self):
        _logger.info(u'ЭМД -ын цахим системээс токен авч жорын дугаараар шалгаж байна')
        '''
            ЭМД -ын цахим системээс токен авч жорын дугаараар шалгах функц
        '''
        check_number = self.name
        register_number = self.register
        config_id = self.config_id
        recipt_data = {}
        json_data = []
        access_token = ''
        error_message = ''
        head = {'Authorization': 'Basic VV9mZl05Qmp5WlhMbUcmZHcmOlo3JHtFenlyRDRheUN9RkxkJg=='}
        data = {
            'grant_type': 'password',
            'username': config_id.user_name,
            'password': config_id.password,
        }
        emd_url = 'https://ws.emd.gov.mn/oauth/token?'
        response = requests.post(emd_url, params=data, headers=head, verify=False)
        if response.status_code == 200:
            new_data = json.loads(response.text)
            access_token = new_data['access_token']
            _logger.info(u' %s дугаартай жороор ЭМД-н системээс авсан токен %s' % (self.name, access_token))
                    
            _logger.warn(u' %s insurance.id' % (self.id))
            self.send_emd_recept(access_token)
        else:
            error_message = u'ЭМД-ийн системтэй холбогдоход алдаа гарлаа'
            _logger.error(u'%s дугаартай жороор ЭМД-н системээс токен авахад алдаа гарлаа.' % self.name)
            if self:
                raise osv.except_osv(_(u'ЭМД системтэй холбогдож чадсангүй!'),error_message)
        return True

    def  send_emd_recept(self, access_token):
        '''
        ЭМД -ын цахим системээс токен авч жорын дугаараар шалгах функц
        '''
        # insurance = self.env['pos.insurance.sale'].browse(insurance_id)
        insu_line = self.insurance_line
        new_data = False
        if insu_line and access_token:
            ebarimtDetails = []
            totalAmt = 0.0
            insAmt = 0.0
            detCnt = 0
#             insurance.totalAmt = insurance.insAmt = insurance.netAmt = 0
            insurance_date = self.date
            # dt = datetime.strptime(insurance_date[0], '%Y-%m-%d %H:%M:%S')
            # dt = dt.date()
            unix_secs = int(mktime(insurance_date.timetuple())) * 1000
            for line in insu_line:
                totalAmt = line.price * line.quantity - line.totalAmt
                insAmt = line.totalAmt
                _logger.info(u'prod name==%s'%line.product_id.name)
                detCnt +=1
                
                if line.product_id.name != None:
                    ebarimtDetails.append({
                        'detailId': line.detail_id,
                        'tbltId': line.product_id.insurance_list_id.tbltId,
                        'barCode' :line.product_id.insurance_list_id.tbltBarCode,
                        'productName': line.product_id.name.encode('utf-8').strip(),
                        'quantity': line.quantity * line.product_id.package_qty if line.product_id.package_qty != 0 else line.quantity,
                        'price':line.price,
                        'insAmt':line.insAmt,
                        'totalAmt':line.price * line.quantity - line.insAmt
                        })
                    _logger.info(u'totalAmt = %s, insAmt=%s, netAmt = %s' %(self.totalAmt, self.insAmt, self.netAmt))
            
            vals  = {
                "receiptId": int(self.receipt_id),
                "posRno": str(self.origin.bill_id),
                "salesDate": unix_secs,
                "totalAmt": self.totalAmt,    # order.get_total_with_tax().toFixed(2),
                "status": 1,
                "insAmt": self.insAmt,
                "vatAmt": self.netAmt - self.netAmt/1.1,
                "netAmt":  self.netAmt,
                "receiptNumber": int(self.name),
                "detCnt": detCnt,
                "ebarimtDetails": ebarimtDetails,
                "lastName": self.lastName,
                "firstName": self.firstName,
                "register": self.register,
            } 
            
            head = {"Content-Type": "application/json"}
            myUrl = 'https://ws.emd.gov.mn/ebarimt/send?access_token=' + access_token
            _logger.info(u'URL мэдээлэл : %s', myUrl)
            _logger.info(u'head мэдээлэл : %s', head)
            
            emd_datas = json.dumps(vals)
            _logger.info(u'emd_datas мэдээлэл : %s', emd_datas)
            _logger.info(u'emd_datas type : %s', type(emd_datas))

            response1 = requests.post(myUrl, headers=head, data=emd_datas, verify=False)
            _logger.info(u'response1 мэдээлэл : %s', response1)
            if response1.text:
                new_data = json.loads(response1.text)
                if new_data['code'] != '200':
                    _logger.error(u'ЭМД системтэй холбогдож чадсангүй!. %s', new_data)
                    raise ValidationError(u'ЭМД системтэй холбогдож чадсангүй!')

                else:
                    self.write({'state': 'sented'})
        return True


class PosInsuranceSaleLine(models.Model):
    _name = "pos.insurance.sale.line"
    _description = "POS sale order line Health Insurance"

    product_id = fields.Many2one('product.product', 'Product Name')
    quantity = fields.Float('Quantity')
    price = fields.Float('Price')
    totalAmt = fields.Float('Total Amount')
    insAmt = fields.Float('Insurance Amount')
    parent_id = fields.Many2one('pos.insurance.sale', 'Parent')
    detail_id = fields.Integer('Detail ID')
    intern_name = fields.Char('International Name')
    date = fields.Datetime('Date', related='parent_id.date', readonly=True)
    config_id = fields.Many2one(string='POS Configure', related='parent_id.config_id', readonly=True)
    product_category_id = fields.Many2one(string='POS Configure', related='product_id.categ_id', readonly=True)
    tbltId = fields.Integer('Tablet ID')
    packGroup = fields.Integer('packGroup')

