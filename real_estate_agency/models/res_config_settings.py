# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    re_commission_type = fields.Selection(
        related='company_id.re_commission_type', readonly=False)
    re_commission_rate = fields.Float(
        related='company_id.re_commission_rate', readonly=False)

    google_maps_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter='real_estate_agency.google_maps_api_key',
        help='JavaScript API key used by the interactive map. Restrict it by '
             'HTTP referrer in the Google Cloud console.')
