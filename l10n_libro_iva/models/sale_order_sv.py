from odoo import models, fields, api


class SaleOrderDate(models.Model):
    _inherit = 'sale.order'

    date_order = fields.Datetime(string='Fecha de orden', index=True, required=True,
                                 states={'sale': [('readonly', False)], 'done': [('readonly', False)],
                                         'cancel': [('readonly', False)]}, default=fields.Datetime.now,
                                 help="Representa la fecha en la que la Cotización debe validarse y convertirse en una "
                                      "órden de venta")

    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'sale':
            self.date_order = fields.Datetime.now()
