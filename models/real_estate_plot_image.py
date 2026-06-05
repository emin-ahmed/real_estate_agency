# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import fields, models


class RealEstatePlotImage(models.Model):
    """An extra photo of a plot. Plots keep one cover image (image.mixin on the
    plot) plus any number of these gallery photos, shown as a carousel on the
    map popup."""

    _name = 'real.estate.plot.image'
    _description = 'Plot Photo'
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(string='Title')
    sequence = fields.Integer(default=10)
    plot_id = fields.Many2one(
        comodel_name='real.estate.plot', string='Plot',
        required=True, ondelete='cascade')
    # Make the picture itself mandatory (the mixin leaves it optional).
    image_1920 = fields.Image(
        string='Image', max_width=1920, max_height=1920, required=True)
