# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    re_commission_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ],
        string='Default Commission Type', default='percentage')
    re_commission_rate = fields.Float(
        string='Default Commission Rate (%)', default=5.0)
