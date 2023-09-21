from odoo import models, fields, api


class PurchaseReportView(models.Model):
    _inherit = 'purchase.order'

    date_approve = fields.Datetime(string='Fecha de confirmación', index=True, readonly=False)