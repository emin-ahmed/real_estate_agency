# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_plot_buyer = fields.Boolean(string='Is a Buyer')
    is_real_estate_agent = fields.Boolean(string='Is an Agent')

    plot_ids = fields.One2many(
        comodel_name='real.estate.plot', inverse_name='buyer_id',
        string='Purchased Plots')
    plot_purchase_count = fields.Integer(
        string='Plots Bought', compute='_compute_plot_purchase_count',
        store=True)

    @api.depends('plot_ids')
    def _compute_plot_purchase_count(self):
        for partner in self:
            partner.plot_purchase_count = len(partner.plot_ids)

    def action_view_purchased_plots(self):
        """Open the plots this partner has bought."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Purchased Plots'),
            'res_model': 'real.estate.plot',
            'view_mode': 'list,kanban,form',
            'domain': [('buyer_id', '=', self.id)],
            'context': {'default_buyer_id': self.id},
        }
