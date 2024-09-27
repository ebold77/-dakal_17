# -*- coding: utf-8 -*-

import logging

from zk import ZK
import pytz

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__file__)


class HrAttendanceDevice(models.Model):
    _name = "hr.attendance.device"
    _description = 'Attendance Device'

    name = fields.Char('Name', required=True)
    ip = fields.Char('Device IP', required=True)
    port = fields.Integer('Port No', required=True)
    use_udp = fields.Boolean('Use UDP port', help='Check this if your device uses UDP port.', default=False)
    password = fields.Char('Password')
    tz = fields.Selection('_tz_get', string='Timezone', required=True, default=lambda self: self.env.user.tz or 'UTC')
    download_automatically = fields.Boolean('Download Automatically')

    # Цагийн бүсийг онооно.
    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    # Ирцийн төхөөрөмжтэй холболт үүсгэнэ.
    def get_connection(self):
        self.ensure_one()

        conn = None
        # ZK instance үүсгэнэ.
        zk = ZK(self.ip, port=self.port, timeout=5, password=self.password, force_udp=self.use_udp, ommit_ping=False)
        try:
            # Төхөөрөмжтэй холбогдоно.
            conn = zk.connect()
            # Төхөөрөмжтэй холбогдох явцад төхөөрөмжийг идэвхигүй болгоно.
            conn.disable_device()
            # Тестийн аудио: Thank You гэж хэлнэ.
            conn.test_voice()
            _logger.info(u"'%s' төхөөрөмж рүү амжилттай холбогдлоо." % self.name)
        except Exception as e:
            raise ValidationError(_('Connection open failed: %s') % e)
        return conn

    # Ирцийн төхөөрөмжөөс холболтыг салгана.
    def close_connection(self, conn):
        self.ensure_one()
        try:
            # Төхөөрөмжийг эргүүлээд идэвхижүүлнэ.
            conn.enable_device()
        except Exception as e:
            raise ValidationError(_('Connection close failed: %s') % e)
        finally:
            if conn:
                conn.disconnect()
                _logger.info(u"'%s' төхөөрөмжийн холболтыг салгалаа." % self.name)

    # Ирцийн төхөөрөмжтэй холболтыг шалгана.
    def test_connection(self):
        self.ensure_one()

        conn = self.get_connection()

        firmware_version = conn.get_firmware_version()
        platform = conn.get_platform()
        device_name = conn.get_device_name()
        mac_address = conn.get_mac()
        zktime = conn.get_time()
        conn.read_sizes()

        raise UserError(_("Connection is successful.\nFIRMWARE VERSION: %s\nPLATFORM: %s\nDEVICE NAME: %s\nMAC ADDRESS: %s\nTIME: %s\n USAGE: %s") % (firmware_version, platform, device_name, mac_address, zktime, conn))

        self.close_connection(conn)
