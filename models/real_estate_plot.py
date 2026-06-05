# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import api, fields, models


class RealEstatePlot(models.Model):
    """A plot of land (parcelle) — the core inventory item. May belong to a
    lotissement or be sold standalone. Carries location, area, price and a
    lifecycle state (available / reserved / sold)."""

    _name = 'real.estate.plot'
    _description = 'Land Plot (Parcelle)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'reference'

    name = fields.Char(
        string='Name', compute='_compute_name', store=True)
    reference = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: ('New'))
    plot_number = fields.Char(string='Plot Number')

    lotissement_id = fields.Many2one(
        comodel_name='real.estate.lotissement', string='Lotissement',
        ondelete='set null',
        help='Leave empty for a standalone plot not part of a subdivision.')

    surface = fields.Float(string='Surface (m²)')
    price = fields.Monetary(
        string='Price', currency_field='currency_id')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)

    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    address = fields.Char(string='Address')
    moughataa_id = fields.Many2one(
        comodel_name='real.estate.moughataa', string='Moughataa')
    neighborhood = fields.Char(string='Neighborhood')

    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('reserved', 'Reserved'),
            ('sold', 'Sold'),
        ],
        string='Status', default='available', required=True,
        tracking=True, index=True)

    tag_ids = fields.Many2many(
        comodel_name='real.estate.tag', string='Tags')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    @api.depends('reference', 'plot_number')
    def _compute_name(self):
        for plot in self:
            if plot.plot_number:
                plot.name = '%s (N° %s)' % (plot.reference, plot.plot_number)
            else:
                plot.name = plot.reference

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference') or vals['reference'] == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'real.estate.plot') or 'New'
        return super().create(vals_list)

    # Statusbar buttons -----------------------------------------------------
    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_reserved(self):
        self.write({'state': 'reserved'})

    def action_set_sold(self):
        self.write({'state': 'sold'})
