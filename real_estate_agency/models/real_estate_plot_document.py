# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import fields, models


class RealEstatePlotDocument(models.Model):
    """A document attached to a plot — title deed (titre foncier) scans,
    survey plans, contracts, etc."""

    _name = 'real.estate.plot.document'
    _description = 'Plot Document'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=10)
    doc_type = fields.Selection(
        selection=[
            ('titre_foncier', 'Titre foncier'),
            ('plan', 'Plan'),
            ('contrat', 'Contract'),
            ('other', 'Other'),
        ],
        string='Type', default='other', required=True)
    plot_id = fields.Many2one(
        comodel_name='real.estate.plot', string='Plot',
        required=True, ondelete='cascade')
    attachment = fields.Binary(string='File', required=True, attachment=True)
    file_name = fields.Char(string='File Name')
