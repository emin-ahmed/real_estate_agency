# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    property_type = fields.Selection(
        selection=[
            ('land', 'Land'),
            ('house', 'House'),
            ('duplex', 'Duplex'),
        ],
        string='Property Type', default='land', required=True)

    lotissement_id = fields.Many2one(
        comodel_name='real.estate.lotissement', string='Lotissement',
        ondelete='set null',
        help='Leave empty for a standalone plot not part of a subdivision.')

    # Cadastral details, mostly relevant for land parcels.
    zone = fields.Char(string='Region')
    elevation = fields.Float(string='Elevation (m)', digits=(8, 2))
    sides = fields.Char(
        string='Sides', help='Length of each side, e.g. "30m 20m 30m 20m".')

    surface = fields.Float(string='Surface (m²)')
    price = fields.Monetary(
        string='Price', currency_field='currency_id')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        default=lambda self: self._default_currency())

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

    description = fields.Html(string='Description', sanitize_style=True)

    image_ids = fields.One2many(
        comodel_name='real.estate.plot.image', inverse_name='plot_id',
        string='Photos')
    document_ids = fields.One2many(
        comodel_name='real.estate.plot.document', inverse_name='plot_id',
        string='Documents')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    # --- Reservation (stamped automatically when marked reserved) ----------
    reserved_by_id = fields.Many2one(
        comodel_name='res.users', string='Reserved By', readonly=True,
        copy=False)
    reservation_date = fields.Date(
        string='Reservation Date', readonly=True, copy=False)

    # --- Sale information (filled when reserved/sold) ----------------------
    buyer_id = fields.Many2one(
        comodel_name='res.partner', string='Buyer', ondelete='restrict',
        copy=False, tracking=True)
    sale_date = fields.Date(string='Sale Date', copy=False, tracking=True)
    sale_price = fields.Monetary(
        string='Sale Price', currency_field='currency_id', copy=False,
        tracking=True, help='Agreed price; may differ from the listing price.')
    agent_id = fields.Many2one(
        comodel_name='res.partner', string='Agent', copy=False, tracking=True,
        help='The agent who handled the sale and earns the commission. '
             'Set automatically to the seller when the plot is marked sold.')

    # --- Commission --------------------------------------------------------
    commission_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ],
        string='Commission Type',
        default=lambda self: self.env.company.re_commission_type)
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        default=lambda self: self.env.company.re_commission_rate)
    commission_amount = fields.Monetary(
        string='Fixed Commission', currency_field='currency_id')
    commission_total = fields.Monetary(
        string='Commission', currency_field='currency_id',
        compute='_compute_commission_total', store=True)

    @api.depends('reference', 'plot_number')
    def _compute_name(self):
        for plot in self:
            if plot.plot_number:
                plot.name = '%s (N° %s)' % (plot.reference, plot.plot_number)
            else:
                plot.name = plot.reference

    @api.depends('sale_price', 'commission_type', 'commission_rate',
                 'commission_amount')
    def _compute_commission_total(self):
        for plot in self:
            if plot.commission_type == 'fixed':
                plot.commission_total = plot.commission_amount
            elif plot.commission_type == 'percentage':
                plot.commission_total = (
                    plot.sale_price * plot.commission_rate / 100.0)
            else:
                plot.commission_total = 0.0

    @api.constrains('state', 'buyer_id', 'sale_price')
    def _check_sold_requirements(self):
        for plot in self:
            if plot.state == 'sold' and (
                    not plot.buyer_id or not plot.sale_price):
                raise ValidationError(self.env._(
                    'A sold plot (%s) requires a buyer and a sale price.',
                    plot.reference))

    @api.model
    def get_map_config(self):
        """Configuration the map client action needs (read by any internal
        Real Estate user). The API key lives in a system parameter."""
        key = self.env['ir.config_parameter'].sudo().get_param(
            'real_estate_agency.google_maps_api_key', default='')
        return {'google_maps_api_key': key}

    @api.model
    def _default_currency(self):
        """The agency operates in MRU; fall back to the company currency only
        if MRU is somehow unavailable."""
        return self.env.ref('base.MRU', raise_if_not_found=False) \
            or self.env.company.currency_id

    @api.model
    def get_dashboard_data(self):
        """Aggregates for the manager dashboard client action."""
        Plot = self.env['real.estate.plot']
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)

        all_plots = Plot.search([])
        by_state = {
            'available': len(all_plots.filtered(lambda p: p.state == 'available')),
            'reserved': len(all_plots.filtered(lambda p: p.state == 'reserved')),
            'sold': len(all_plots.filtered(lambda p: p.state == 'sold')),
        }

        sold_month = Plot.search([
            ('state', '=', 'sold'),
            ('sale_date', '>=', month_start),
            ('sale_date', '<=', today),
        ])

        sold_all = Plot.search([('state', '=', 'sold')])
        agents = {}
        for plot in sold_all:
            grp = agents.setdefault(plot.agent_id.id, {
                'name': plot.agent_id.display_name or 'Unassigned',
                'count': 0,
                'commission': 0.0,
            })
            grp['count'] += 1
            grp['commission'] += plot.commission_total
        top_agents = sorted(
            agents.values(), key=lambda a: a['commission'], reverse=True)[:5]

        by_moughataa = []
        for moughataa in all_plots.mapped('moughataa_id'):
            recs = all_plots.filtered(lambda p: p.moughataa_id == moughataa)
            by_moughataa.append({
                'name': moughataa.display_name,
                'total': len(recs),
                'available': len(recs.filtered(lambda p: p.state == 'available')),
                'reserved': len(recs.filtered(lambda p: p.state == 'reserved')),
                'sold': len(recs.filtered(lambda p: p.state == 'sold')),
            })
        by_moughataa.sort(key=lambda d: d['total'], reverse=True)

        currency = self._default_currency()
        return {
            'total': len(all_plots),
            'by_state': by_state,
            'sales_month_count': len(sold_month),
            'revenue_month': sum(sold_month.mapped('sale_price')),
            'commission_month': sum(sold_month.mapped('commission_total')),
            'top_agents': top_agents,
            'by_moughataa': by_moughataa,
            'currency_symbol': currency.symbol or '',
        }

    @api.model
    def get_plot_images(self, plot_id):
        """Base64 photos for the map popup carousel: the cover image first,
        then the gallery photos, all at the 512px size."""
        plot = self.browse(plot_id).exists()
        if not plot:
            return []
        images = []
        if plot.image_512:
            images.append(plot.image_512)
        for photo in plot.image_ids:
            if photo.image_512:
                images.append(photo.image_512)
        return images

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference') or vals['reference'] == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'real.estate.plot') or 'New'
        plots = super().create(vals_list)
        plots._flag_buyers()
        return plots

    def write(self, vals):
        res = super().write(vals)
        if vals.get('buyer_id'):
            self._flag_buyers()
        return res

    def _flag_buyers(self):
        """Mark the assigned buyers as real-estate buyers so they show up in
        the buyer selector and the Buyers list."""
        to_flag = self.mapped('buyer_id').filtered(lambda p: not p.is_plot_buyer)
        if to_flag:
            to_flag.is_plot_buyer = True

    # Statusbar buttons -----------------------------------------------------
    def action_set_available(self):
        self.write({
            'state': 'available',
            'reserved_by_id': False,
            'reservation_date': False,
        })

    def action_set_reserved(self):
        self.write({
            'state': 'reserved',
            'reserved_by_id': self.env.user.id,
            'reservation_date': fields.Date.context_today(self),
        })

    def action_set_sold(self):
        for plot in self:
            if not plot.buyer_id or not plot.sale_price:
                raise UserError(self.env._(
                    'Set a buyer and a sale price on plot %s before marking '
                    'it as sold.', plot.reference))
            vals = {'state': 'sold'}
            if not plot.sale_date:
                vals['sale_date'] = fields.Date.context_today(plot)
            plot.write(vals)
