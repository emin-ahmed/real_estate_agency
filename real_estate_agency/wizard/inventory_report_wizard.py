# Part of the real_estate_agency module. See LICENSE file for details.
from odoo import api, fields, models


def _counts(records):
    return {
        'total': len(records),
        'available': len(records.filtered(lambda p: p.state == 'available')),
        'reserved': len(records.filtered(lambda p: p.state == 'reserved')),
        'sold': len(records.filtered(lambda p: p.state == 'sold')),
    }


class InventoryReportWizard(models.TransientModel):
    _name = 'real.estate.inventory.report.wizard'
    _description = 'Inventory Report Wizard'

    moughataa_id = fields.Many2one(
        comodel_name='real.estate.moughataa', string='Moughataa')
    lotissement_id = fields.Many2one(
        comodel_name='real.estate.lotissement', string='Lotissement')

    def action_print(self):
        self.ensure_one()
        data = {
            'moughataa_id': self.moughataa_id.id or False,
            'lotissement_id': self.lotissement_id.id or False,
        }
        return self.env.ref(
            'real_estate_agency.action_report_inventory'
        ).report_action(self, data=data)


class ReportInventory(models.AbstractModel):
    _name = 'report.real_estate_agency.report_inventory'
    _description = 'Inventory Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        domain = []
        if data.get('moughataa_id'):
            domain.append(('moughataa_id', '=', data['moughataa_id']))
        if data.get('lotissement_id'):
            domain.append(('lotissement_id', '=', data['lotissement_id']))
        plots = self.env['real.estate.plot'].search(domain)

        by_moughataa = []
        for moughataa in plots.mapped('moughataa_id'):
            recs = plots.filtered(lambda p: p.moughataa_id == moughataa)
            by_moughataa.append(dict(name=moughataa.display_name, **_counts(recs)))
        orphan_m = plots.filtered(lambda p: not p.moughataa_id)
        if orphan_m:
            by_moughataa.append(dict(name='Unspecified', **_counts(orphan_m)))

        by_lotissement = []
        for lot in plots.mapped('lotissement_id'):
            recs = plots.filtered(lambda p: p.lotissement_id == lot)
            by_lotissement.append(dict(name=lot.display_name, **_counts(recs)))
        standalone = plots.filtered(lambda p: not p.lotissement_id)
        if standalone:
            by_lotissement.append(dict(name='Standalone', **_counts(standalone)))

        return {
            'doc_ids': docids,
            'doc_model': 'real.estate.inventory.report.wizard',
            'docs': self.env['real.estate.inventory.report.wizard'].browse(docids),
            'by_state': _counts(plots),
            'by_moughataa': sorted(by_moughataa, key=lambda d: d['name']),
            'by_lotissement': sorted(by_lotissement, key=lambda d: d['name']),
        }
