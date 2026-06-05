# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import api, fields, models


class RealEstateLotissement(models.Model):
    """A lotissement (subdivision / land development project). Groups the plots
    an agency markets together. An agency manages many lotissements."""

    _name = 'real.estate.lotissement'
    _description = 'Lotissement (Subdivision)'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Reference Code', required=True, tracking=True)
    location = fields.Char(string='Location')
    moughataa_id = fields.Many2one(
        comodel_name='real.estate.moughataa', string='Moughataa')
    planned_plots = fields.Integer(
        string='Planned Plots',
        help='Total number of plots this lotissement is planned to contain.')

    plot_ids = fields.One2many(
        comodel_name='real.estate.plot', inverse_name='lotissement_id',
        string='Plots')

    plot_count = fields.Integer(
        string='Total Plots', compute='_compute_plot_counts')
    available_count = fields.Integer(
        string='Available', compute='_compute_plot_counts')
    reserved_count = fields.Integer(
        string='Reserved', compute='_compute_plot_counts')
    sold_count = fields.Integer(
        string='Sold', compute='_compute_plot_counts')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    _code_uniq = models.Constraint(
        'unique(code)',
        'The reference code must be unique.',
    )

    @api.depends('plot_ids.state')
    def _compute_plot_counts(self):
        for lotissement in self:
            plots = lotissement.plot_ids
            lotissement.plot_count = len(plots)
            lotissement.available_count = len(
                plots.filtered(lambda p: p.state == 'available'))
            lotissement.reserved_count = len(
                plots.filtered(lambda p: p.state == 'reserved'))
            lotissement.sold_count = len(
                plots.filtered(lambda p: p.state == 'sold'))

    def action_view_plots(self):
        """Open the plots belonging to this lotissement."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'real.estate.plot',
            'view_mode': 'list,kanban,form',
            'domain': [('lotissement_id', '=', self.id)],
            'context': {'default_lotissement_id': self.id},
        }
