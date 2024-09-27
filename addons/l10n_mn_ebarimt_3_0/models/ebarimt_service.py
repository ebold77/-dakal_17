# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import models, fields
import traceback
import requests
import urllib
import urllib.request as urllib2
from urllib.error import HTTPError
import json
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class ebarimt_service(models.Model):
    _name = "ebarimt.service"
    _description = 'Mongolian VAT information service'

    def getInformation(self, showInfo=False, host=False, port= False):
        res = False
        
        ebarimt_url = "http://" + host +':'+ port+"/rest/info"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.get(url=ebarimt_url, headers=headers)
        print('response==============>>>', response.text)
        if response:
            try:
                res = json.loads(response.text)
                if 'extraInfo' in res and res['extraInfo'].get('lastSentDate', False) is None:
                    res['extraInfo']['lastSentDate'] = False
            except Exception:
                error_message = traceback.format_exc()
                _logger.error(error_message)
        if showInfo:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message']= ('Operator Name: %s, Operator Tin: %s, pos Id: %s, db Dir Path: %s, count Lottery: %s') %(res['operatorName'], res['operatorTIN'], res['posId'], res['appInfo']['currentDir'], res['leftLotteries'])
            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }


    # def checkApi(self, showInfo=False, host=False, port= False):
        
    #     res = False
        
    #     try:
    #         res = urllib2.urlopen("http://%s:%s/checkAPI/" % (host, port)).read()
    #         res = json.loads(res)
    #     except Exception:
    #         error_message = traceback.format_exc()
    #         _logger.error(error_message)
         
    #     data = res
    #     # print('data===>>', data)
    #     if not data['config']['success']:
    #         self.sendData(False)

    #     if not data['database']['success']:
    #         raise UserError(_('Database error message: %s ')% data['database']['message'])

    #     if not data['config']['success']:
    #         raise UserError(_('Config error message: %s ')% data['config']['message'])

    #     if not data['network']['success']:
    #         raise UserError(_('Network error message: %s ')% data['network']['message'])

    #     if showInfo:
    #         view = self.env.ref('sh_message.sh_message_wizard')
    #         view_id = view and view.id or False
    #         context = dict(self._context or {})
    #         if data['config']['success']:
    #             name = 'Success'
    #             context['message']=_("EBarimt connection successful.")
    #         else:
    #             name = 'Error'
    #             context['message']=_("EBarimt connection was not successful.")

    #         return {
    #             'name': name,
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'sh.message.wizard',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'context': context,
    #         }


    def sendData(self, showInfo=False, host=False, port= False):
        res = False
        print('host----------', host, port)
        ebarimt_url = "http://" + host +':'+ port+"/rest/sendData"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        response = requests.get(url=ebarimt_url, headers=headers)
        # print('response==============>>>', response.text)
        # if response:
        #     try:
        #         res = json.loads(response.text)
        #     except Exception:
        #         error_message = traceback.format_exc()
        #         _logger.error(error_message)

        # if showInfo:
        #     view = self.env.ref('sh_message.sh_message_wizard')
        #     view_id = view and view.id or False
        #     context = dict(self._context or {})
        #     if res['success']:
        #         name = 'Success'
        #         context['message']=_("EBarimt data sent successfully.")
        #     else:
        #         name = 'Error'
        #         context['message']=_("EBarimt data could not sent. Check your EBarimt connection.")

        #     return {
        #         'name': name,
        #         'type': 'ir.actions.act_window',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'res_model': 'sh.message.wizard',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'context': context,
        #     }
       


    # def put(self, data='',host=False, port= False):
    #     _logger.info("put request: %s", data)
        
    #     result_info = self.getInformation(showInfo=False, host = host, port = port)

    #     if int(result_info['extraInfo']['countBill']) >= 9999:
    #         sendData(showInfo=False, host = host, port = port)
    #     # d = json.dumps(data)
    #     # _logger.info('PUT JSON DATA :: %s' % d)
    #     json_arg = urllib.parse.urlencode({"param": data}).encode("utf-8")
    #     # print('JSON ARG=====',json_arg)
    #     req = urllib.request.Request("http://%s:%s/put/" % (host, port))

    #     try:
    #         res = urllib2.urlopen(req,data=json_arg).read()
    #         result = json.loads(res)
            
    #     except HTTPError as e:
    #         content = e.read()
        
    #     if not result['success']:
    #         raise UserError(_('Error occurred when putting VAT data. Error code: %s Message: %s')% (result['errorCode'], result['message']))

    #     if 'lotteryWarningMsg' in result:
    #         if result['lotteryWarningMsg']:
    #             raise UserError(_('Error occurred when putting VAT data: %s')% result['lotteryWarningMsg'])

    #     return result

    # def returnBill(self, data='', host=False, port= False):
    #     res = False
    #     try:

    #         json_arg = urllib.parse.urlencode({"param": data}).encode("utf-8")
    #         # print('JSON ARG=====',json_arg, type(json_arg))
    #         request = urllib2.Request("http://%s:%s/returnBill/" % (host, port))

    #         res = urllib2.urlopen(request, data=json_arg).read()
    #         result = json.loads(res)
    #     except Exception:
    #         error_message = traceback.format_exc()
    #         _logger.error(error_message)
    #         result = {
    #             'success': False, 'errorCode': 'local', 'message': error_message
    #         }

    #     if not result['success']:
    #         raise UserError(_('Error occurred when send VAT data. Error code: %s Error Message: %s')% {result['errorCode'], result['message']})

    #     return result
