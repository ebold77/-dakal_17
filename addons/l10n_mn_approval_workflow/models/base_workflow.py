from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class BaseWorkflow(models.AbstractModel):
    _name = 'base.workflow'
    _description = 'Base Workflow'

    @api.model
    def _get_module_name(self):
        raise UserError(_('_get_module_name function is not implemented.'))

    @api.model
    def _get_action_name(self):
        raise UserError(_('_get_action_name function is not implemented.'))

    @api.model
    def _get_workflow_id_domain(self):
        return [('model_id.model', '=', self._name)]

    # --------------- BEGIN: APPROVAL WORKFLOW RELATED LOGICS ------------------
    def _get_default_workflow_id(self):
        wf = self.env['approval.workflow'].search([
            ('model_id.model', '=', self._name),
            ('company_id', '=', self.env.company.id)
        ], order='sequence', limit=1)
        return wf.id if wf else False

    def _get_default_workflow_line_id(self):
        if self.workflow_id:
            wfl = self.env['approval.workflow.line'].search([('workflow_id', '=', self.workflow_id.id)], order='sequence', limit=1)
            return wfl.id if wfl else False
        else:
            return False

    workflow_id = fields.Many2one('approval.workflow', string='Approval Workflow', default=_get_default_workflow_id, copy=True, required=True, domain=_get_workflow_id_domain)
    workflow_line_id = fields.Many2one('approval.workflow.line', string='State', default=_get_default_workflow_line_id, copy=False, tracking=True, index=True)
    attributes = fields.Text(related='workflow_line_id.attributes')
    visible_workflow_line_ids = fields.Many2many('approval.workflow.line', compute='_compute_visible_workflow_line_ids', string='Visible Workflow Lines')

    next_line_id = fields.Many2one('approval.workflow.line', related='workflow_line_id.next_line_id', readonly=True)
    prev_line_id = fields.Many2one('approval.workflow.line', related='workflow_line_id.prev_line_id', readonly=True)
    state_type = fields.Char(string='State Type', compute='_compute_state_type', store=True)
    is_edit = fields.Boolean(related="workflow_line_id.is_edit", readonly=True)
    approver_id = fields.Many2one('res.users', 'Approved User', copy=False,)
    history_ids = fields.One2many('base.workflow.history.line', 'workflow_id', string='Approval History', readonly=True)
    signature_html = fields.Html(compute='_compute_signature_html')

    @api.depends('history_ids', 'history_ids.workflow_line_id.name', 'history_ids.workflow_line_id.is_print')
    def _compute_signature_html(self):
        for obj in self:
            html = ''
            if self.history_ids:
                printable_histories = self.history_ids.filtered(lambda h: h.workflow_line_id.is_print)
                if printable_histories:
                    html += '<table>'
                    for history in printable_histories:
                        html += '<tr><td>'
                        html += '<span>%s</span>' % history.workflow_line_id.name
                        html += '<span>: </span>'
                        html += '<span>............................</span>'
                        html += '<span>/</span>'
                        if history.user_id.employee_id and history.user_id.employee_id.last_name:
                            html += history.user_id.employee_id.last_name[:1].upper()
                            html += '.'
                        if history.user_id.employee_id:
                            html += history.user_id.employee_id.name.upper()
                        else:
                            html += '<span>............................</span>'
                        html += '<span>/</span>'
                        html += '</td></tr>'
                    html += '</table>'
            obj.signature_html = html

    ##
    # State type checker
    def is_state_draft(self):
        return self.workflow_line_id.state_type == 'draft' if self.workflow_line_id else False

    def is_state_sent(self):
        return self.workflow_line_id.state_type == 'sent' if self.workflow_line_id else False

    def is_state_done(self):
        return self.workflow_line_id.state_type == 'done' if self.workflow_line_id else False

    def is_state_cancel(self):
        return self.workflow_line_id.state_type == 'cancel' if self.workflow_line_id else False

    ##
    # Callbacks
    def _before_next_workflow_step(self):
        pass

    def _after_next_workflow_step(self):
        pass

    def _when_state_done(self):
        pass

    def _when_state_sent(self):
        pass

    def _when_state_cancel(self):
        pass

    def _before_state_cancel(self):
        pass

    def _when_state_draft(self):
        pass

    def _when_prev_workflow_step(self):
        pass

    def _get_next_workflow_line(self):
        return self.workflow_line_id.get_object_next_line(self)

    @api.depends('workflow_line_id')
    def _compute_state_type(self):
        for base in self:
            base.state_type = base.workflow_line_id.state_type

    @api.depends('workflow_id.line_ids')
    def _compute_visible_workflow_line_ids(self):
        for base in self:
            if base.workflow_id:
                visible_lines = self.env['approval.workflow.line']
                for line in base.workflow_id.line_ids:
                    if eval(str(line.expression), {'object': base}):
                        visible_lines |= line
                base.visible_workflow_line_ids = visible_lines
            else:
                base.visible_workflow_line_ids = self.env['approval.workflow.line']

    @api.onchange('workflow_id')
    def _onchange_workflow_id(self):
        if self.workflow_id:
            self.workflow_line_id = self._get_default_workflow_line_id()
        else:
            self.workflow_line_id = False

    def unlink(self):
        for record in self:
            if record.state_type != 'draft':
                raise UserError(_('You cannot delete a record which is not in draft state: %s.\nFirstly you should cancel and draft it instead.') % record.name_get()[0][1])
        return super(BaseWorkflow, self).unlink()

    def copy(self, default=None):
        record = super().copy(default)
        record.write({
            'workflow_line_id': record._get_default_workflow_line_id(),
        })
        record._compute_state_type()
        return record

    def action_next_workflow_step(self):
        self.ensure_one()
        next_workflow_line = self._get_next_workflow_line()
        if next_workflow_line:
            if next_workflow_line._check_workflow_line_allowed():
                # before state
                self._before_next_workflow_step()
                self.workflow_line_id = next_workflow_line
                # after state
                self._after_next_workflow_step()
                # create history
                prev_history = self.env['base.workflow.history.line'].search([('workflow_id', '=', self.id), ('workflow_line_id', '=', next_workflow_line.id)])
                if prev_history:
                    prev_history.unlink()
                # vals_list = {
                #     'workflow_id': self.id,
                #     'workflow_line_id': next_workflow_line.id,
                #     'user_id': self.env.user.id
                # }
                # self.env['base.workflow.history.line'].create(vals_list)

                next_next_workflow_line = self._get_next_workflow_line()
                self.send_chat(next_next_workflow_line)
                if self.is_state_done():
                    # when state is done
                    self.write({'approver_id': self.env.user.id})
                    self._when_state_done()
                elif self.is_state_sent():
                    # when state is sent
                    self._when_state_sent()
            else:
                allowed_usernames = ', '.join(next_workflow_line.user_ids.mapped('name'))
                raise AccessError('You are not allowed to confirm.\n Allowed users: %s' % allowed_usernames)

    def action_prev_workflow_step(self):
        prev_workflow_line = self.workflow_line_id.get_object_prev_line(self)
        if prev_workflow_line:
            if self.workflow_line_id._check_workflow_line_allowed():
                self.workflow_line_id = prev_workflow_line
                self._when_prev_workflow_step()
                self.send_chat(prev_workflow_line)
            else:
                raise AccessError(_('You are not allowed to back.'))

    def action_cancel_workflow_step(self):
        cancel_workflow_line = self.workflow_line_id._get_cancel_workflow_line()
        if cancel_workflow_line._check_workflow_line_allowed():
            self._before_state_cancel()
            self.workflow_line_id = cancel_workflow_line
            self._when_state_cancel()
            self.send_chat(cancel_workflow_line)
        else:
            raise AccessError(_('You are not allowed to cancel.'))

    def action_draft_workflow_step(self):
        draft_workflow_line = self.workflow_line_id._get_draft_workflow_line()
        if draft_workflow_line._check_workflow_line_allowed():
            self.workflow_line_id = draft_workflow_line
            self._when_state_draft()
            self.send_chat(draft_workflow_line)
        else:
            raise AccessError(_('You are not allowed to draft.'))

    def send_chat(self, workflow_line):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].check_object_reference(self._get_module_name(), self._get_action_name())[1]
        html = """<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=%s&action=%s>%s</a></b> """ % (base_url, self.id, self._name, action_id, self.name_get()[0][1])
        html += 'бүртгэл </br> <b>%s</b> төлөвт шилжлээ.' % self.workflow_line_id.name

        if workflow_line.state_type not in ('sent', 'done'):
            partners = self.create_uid.partner_id
        else:
            partners = workflow_line.user_ids.mapped('partner_id')

        self.workflow_line_id.send_chat(html, partners)

    # --------------- END: APPROVAL WORKFLOW RELATED LOGICS ------------------

    def force_workflow_step_to_done(self):
        self.ensure_one()
        self.workflow_line_id = self._get_default_workflow_line_id()
        if not self.is_state_done():
            self.workflow_line_id = self.workflow_line_id._get_done_workflow_line()
        self._when_state_done()

    def force_workflow_step_to_cancel(self):
        self.ensure_one()
        if not self.is_state_cancel():
            self.action_cancel_workflow_step()

    def force_workflow_step_to_draft(self):
        self.ensure_one()
        self.workflow_line_id = self._get_default_workflow_line_id()

class ApprovalWorkflowHistoryLine(models.Model):
    _name = 'base.workflow.history.line'
    _description = 'Approval Workflow History Line'
    _order = 'create_date'

    workflow_id = fields.Many2one('base.workflow', 'Workflow', required=True)
    workflow_line_id = fields.Many2one('approval.workflow.line', 'State', required=True)
    user_id = fields.Many2one('res.users', 'User', required=True)
