# Part of the real_estate_agency module. See LICENSE file for details.
{
    'name': 'Real Estate Agency (Mauritania)',
    'version': '19.0.6.1.0',
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
    'maintainer': 'Emin Ahmed',
    'website': 'https://github.com/emin-ahmed',
    'images': [
        'static/description/screenshot_map.jpg',
        'static/description/screenshot_dashboard.png',
        'static/description/screenshot_plot.jpg',
    ],
    'depends': ['base', 'mail'],
    'data': [
        'security/real_estate_security.xml',
        'security/ir.model.access.csv',
        'data/res_currency_data.xml',
        'data/ir_sequence_data.xml',
        'data/real_estate_moughataa_data.xml',
        'data/real_estate_tag_data.xml',
        'report/real_estate_reports.xml',
        'report/real_estate_report_templates.xml',
        'views/real_estate_plot_views.xml',
        'views/real_estate_lotissement_views.xml',
        'views/real_estate_commission_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/real_estate_config_views.xml',
        'views/real_estate_map_views.xml',
        'views/real_estate_dashboard_views.xml',
        'views/real_estate_menus.xml',
        'wizard/real_estate_report_wizard_views.xml',
    ],
    'demo': [
        'demo/real_estate_partners_demo.xml',
        'demo/real_estate_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Map client action. Google Maps JS is loaded at runtime from
            # Google's servers using the API key configured in Settings.
            'real_estate_agency/static/src/**/*.js',
            'real_estate_agency/static/src/**/*.xml',
            'real_estate_agency/static/src/**/*.scss',
        ],
    },
    'application': True,
    'installable': True,
}
