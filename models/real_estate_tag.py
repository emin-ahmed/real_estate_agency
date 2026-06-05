# Part of the real_estate_agency module. See LICENSE file for details.
from random import randint

from odoo import fields, models


class RealEstateTag(models.Model):
    """A free-form tag/label for plots (e.g. "Titre foncier", "Viabilisé").
    Mirrors the crm.tag pattern: name + random colour index."""

    _name = 'real.estate.tag'
    _description = 'Real Estate Tag'
    _order = 'name'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)

    _name_uniq = models.Constraint(
        'unique(name)',
        'A tag with this name already exists.',
    )
