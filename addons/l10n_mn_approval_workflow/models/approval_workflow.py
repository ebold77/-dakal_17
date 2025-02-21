from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ApprovalWorkflow(models.Model):
    _name = 'approval.workflow'
    _description = 'Approval Workflow'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    model_id = fields.Many2one('ir.model', string="Approval Model", required=True, ondelete='cascade')
    line_ids = fields.One2many('approval.workflow.line', 'workflow_id', string='Approval Lines', required=True, copy=True)
    line_count = fields.Integer(compute='_compute_line_count')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)

    def _compute_line_count(self):
        for wf in self:
            wf.line_count = len(wf.line_ids)

    def button_generate_steps(self):
        self.ensure_one()
        self.line_ids.unlink()
        self.line_ids.create([
            {
                'state_type': 'draft',
                'sequence': 1,
                'name': _('Draft'),
                'workflow_id': self.id,
            },
            {
                'state_type': 'sent',
                'sequence': 2,
                'name': _('Sent'),
                'workflow_id': self.id,
            },
            {
                'state_type': 'done',
                'sequence': 3,
                'name': _('Done'),
                'workflow_id': self.id,
                'is_edit': False,
            },
            {
                'state_type': 'cancel',
                'sequence': 4,
                'name': _('Cancelled'),
                'workflow_id': self.id,
            },
        ])

    def write(self, vals):
        if 'line_ids' in vals:
            new_lines = []
            counter = 0
            for line in vals['line_ids']:
                if isinstance(line[2], dict):
                    line[2].update({'sequence': counter})
                elif line[0] != 2:
                    line[2] = {'sequence': counter}
                if line[0] != 2:
                    counter = counter + 1
                new_lines.append(line)
            vals['line_ids'] = new_lines
        return super(ApprovalWorkflow, self).write(vals)

    def _find_workflow_line(self, state):
        self.ensure_one()
        return self.line_ids.filtered(lambda l: l.state_type == state)

    def get_cancel_workflow_line(self):
        self.ensure_one()
        return self._find_workflow_line('cancel')

    def get_draft_workflow_line(self):
        self.ensure_one()
        return self._find_workflow_line('draft')

    def get_done_workflow_line(self):
        self.ensure_one()
        return self._find_workflow_line('done')

class ApprovalWorkflowLine(models.Model):
    _name = 'approval.workflow.line'
    _description = 'Approval Workflow Line'
    _order = 'sequence, id'

    name = fields.Char('Step Name')
    workflow_id = fields.Many2one('approval.workflow', string='Approval Workflow', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', required=True)
    state_type = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='State type', required=True)
    expression = fields.Text(string='Expression', default='True', help='Python code using "object" variable. This stage will be executed when If expression result is True, otherwise will be pass.')
    attributes = fields.Text(string='Attributes',)
    is_edit = fields.Boolean(string='Is Edit', default=True)
    user_ids = fields.Many2many('res.users', 'approval_workflow_line_res_users_rel', 'line_id', 'user_id', string='Users')
    is_print = fields.Boolean(string='Is Print', default=False)
    next_line_id = fields.Many2one('approval.workflow.line', 'Next Step', compute='_compute_workflow_line_id')
    prev_line_id = fields.Many2one('approval.workflow.line', 'Previous Step', compute='_compute_workflow_line_id')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name, workflow_id)', 'Name must be unique!')
    ]

    @api.depends('sequence', 'workflow_id', 'state_type')
    def _compute_workflow_line_id(self):
        for line in self:
            line.next_line_id = line._get_next_line()
            line.prev_line_id = line._get_prev_line()

    def _check_workflow_line_allowed(self):
        self.ensure_one()
        if self.user_ids:
            if self.env.user in self.user_ids:
                return True
            else:
                return False
        else:
            return True

    def _get_next_line(self):
        if self.id:
            next_flow_line = self.env['approval.workflow.line'].search([
                ('workflow_id', '=', self.workflow_id.id),
                ('id', '!=', self.id),
                ('sequence', '>', self.sequence),
                ('state_type', 'not in', ['cancel']),
            ], limit=1)
            return next_flow_line
        else:
            return False

    def _get_prev_line(self):
        if self.id:
            prev_flow_line = self.env['approval.workflow.line'].search([
                ('workflow_id', '=', self.workflow_id.id),
                ('id', '!=', self.id),
                ('sequence', '<', self.sequence),
                ('state_type', 'not in', ['cancel']),
            ], limit=1, order="sequence desc")
            return prev_flow_line
        return False

    def _find_workflow_line(self, state):
        return self.env['approval.workflow.line'].search([
            ('workflow_id', '=', self.workflow_id.id),
            ('id', '!=', self.id),
            ('state_type', '=', state),
        ], limit=1)

    def _get_cancel_workflow_line(self):
        return self._find_workflow_line('cancel')

    def _get_draft_workflow_line(self):
        return self._find_workflow_line('draft')

    def _get_done_workflow_line(self):
        return self._find_workflow_line('done')

    def get_object_next_line(self, target):
        self.ensure_one()
        next_workflow_line = self._get_next_line()
        if next_workflow_line:
            visible_lines = self.env['approval.workflow.line']
            for line in target.workflow_id.line_ids:
                if eval(str(line.expression), {'object': target}):
                    visible_lines |= line
            if visible_lines and next_workflow_line not in visible_lines:
                check_next_workflow_line = next_workflow_line
                while check_next_workflow_line not in visible_lines:
                    temp_stage = check_next_workflow_line._get_next_line()
                    if temp_stage == check_next_workflow_line or not temp_stage:
                        break
                    check_next_workflow_line = temp_stage
                next_workflow_line = check_next_workflow_line
        return next_workflow_line

    def get_object_prev_line(self, target):
        self.ensure_one()
        prev_workflow_line = self._get_prev_line()
        if prev_workflow_line:
            visible_lines = self.env['approval.workflow.line']
            for line in target.workflow_id.line_ids:
                if eval(str(line.expression), {'object': target}):
                    visible_lines |= line
            if visible_lines and prev_workflow_line not in visible_lines:
                check_prev_workflow_line = prev_workflow_line
                while check_prev_workflow_line not in visible_lines:
                    temp_stage = check_prev_workflow_line._get_prev_line()
                    if temp_stage == check_prev_workflow_line or not temp_stage:
                        break
                    check_prev_workflow_line = temp_stage
                prev_workflow_line = check_prev_workflow_line
        return prev_workflow_line

    def send_chat(self, html, partners):
        if not partners:
            if not self.user_ids:
                return True
            raise UserError('Not exist user for notification.')

        channel_obj = self.env['discuss.channel']
        for partner in partners:
            if self.env.user.partner_id != partner:
                notification_ids = [(0, 0, {
                        'res_partner_id': partner.id,
                        'notification_type': 'inbox'
                        })]
                partner_ids = partner.ids
                channel = self.env['discuss.channel'].channel_get([partner.id])
                channel_id = self.env['discuss.channel'].browse(channel["id"])
                notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (channel_id.id, channel_id.name,)
                channel_id.message_post(
                        body=html,
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment',
                        partner_ids=partner_ids,
                        notification_ids=notification_ids
                )
                # # send mail
                # partner_user = partner.user_ids[0] if partner.user_ids else False
                # if partner_user and partner_user.notification_type == 'email':
                #     self.send_mail(html, partner)

    def send_mail(self, html, partner):
        outgoing_email = self.env['ir.mail_server'].sudo().search([])
        if not outgoing_email:
            raise UserError(_('There is no configuration for outgoing mail server. Please contact system administrator.'))

        vals = {
            'state': 'outgoing',
            'subject': self.remove_html_tags(html),
            'body_html': html,
            'email_to': partner.email,
            'reply_to': self.env.user.email,
            'email_from': outgoing_email.smtp_user
        }
        self.env['mail.mail'].sudo().create(vals).send()

    def remove_html_tags(self, text):
        """Remove html tags from a string"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
