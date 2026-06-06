# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import api, fields, models


class CommissionReportWizard(models.TransientModel):
    _name = 'real.estate.commission.report.wizard'
    _description = 'Commission Report Wizard'

    date_from = fields.Date(
        string='From', required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(
        string='To', required=True, default=fields.Date.context_today)
    agent_id = fields.Many2one(
        comodel_name='res.partner', string='Agent',
        help='Leave empty to include every agent.')

    def action_print(self):
        self.ensure_one()
        data = {
            'date_from': fields.Date.to_string(self.date_from),
            'date_to': fields.Date.to_string(self.date_to),
            'agent_id': self.agent_id.id or False,
        }
        return self.env.ref(
            'real_estate_agency.action_report_commission'
        ).report_action(self, data=data)


class ReportCommission(models.AbstractModel):
    _name = 'report.real_estate_agency.report_commission'
    _description = 'Commission Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        agent_id = data.get('agent_id')
        domain = [
            ('state', '=', 'sold'),
            ('sale_date', '>=', date_from),
            ('sale_date', '<=', date_to),
        ]
        if agent_id:
            domain.append(('agent_id', '=', agent_id))
        plots = self.env['real.estate.plot'].search(
            domain, order='agent_id, sale_date')

        groups = {}
        for plot in plots:
            grp = groups.setdefault(plot.agent_id.id, {
                'agent': plot.agent_id,
                'plots': self.env['real.estate.plot'],
                'total_sales': 0.0,
                'total_commission': 0.0,
            })
            grp['plots'] |= plot
            grp['total_sales'] += plot.sale_price
            grp['total_commission'] += plot.commission_total
        agent_groups = sorted(
            groups.values(), key=lambda g: g['agent'].display_name or '')

        return {
            'doc_ids': docids,
            'doc_model': 'real.estate.commission.report.wizard',
            'docs': self.env['real.estate.commission.report.wizard'].browse(docids),
            'date_from': date_from,
            'date_to': date_to,
            'agent_groups': agent_groups,
            'grand_sales': sum(g['total_sales'] for g in agent_groups),
            'grand_commission': sum(g['total_commission'] for g in agent_groups),
            'currency': self.env['real.estate.plot']._default_currency(),
        }
