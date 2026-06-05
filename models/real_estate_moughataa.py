# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import fields, models


class RealEstateMoughataa(models.Model):
    """A moughataa (commune/district). Nouakchott has 9; pre-loaded as reference
    data. Used to localise plots and lotissements geographically."""

    _name = 'real.estate.moughataa'
    _description = 'Moughataa (Commune)'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)

    _name_uniq = models.Constraint(
        'unique(name)',
        'A moughataa with this name already exists.',
    )
