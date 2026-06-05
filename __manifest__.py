# Part of the real_estate_agency module. See LICENSE file for details.
{
    'name': 'Real Estate Agency (Mauritania)',
    'version': '19.0.1.0.0',
    'summary': 'Manage land-plot sales, agents and commissions for real estate agencies',
    'description': """
Real Estate Agency (Mauritania)
===============================

Manage a real estate agency that sells plots of land (parcelles), often grouped
into subdivisions/projects (lotissements):

* Inventory of land plots with location, area and status (available/reserved/sold).
* Sales deals linking a buyer to a plot.
* Sales agents and their commissions.

Amounts are in Mauritanian Ouguiya (MRU). Built incrementally on Odoo Community.
""",
    'category': 'Sales',
    'license': 'LGPL-3',
    'author': 'Emin Ahmed',
    'website': 'https://github.com/emin-ahmed',
    'depends': ['base', 'mail'],
    'data': [
        'security/real_estate_security.xml',
        'security/ir.model.access.csv',
        'data/res_currency_data.xml',
        'data/ir_sequence_data.xml',
        'data/real_estate_moughataa_data.xml',
        'data/real_estate_tag_data.xml',
        'views/real_estate_plot_views.xml',
        'views/real_estate_lotissement_views.xml',
        'views/real_estate_config_views.xml',
        'views/real_estate_menus.xml',
    ],
    'demo': [
        'demo/real_estate_demo.xml',
    ],
    'application': True,
    'installable': True,
}
