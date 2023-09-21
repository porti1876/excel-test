from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    scheduled_date = fields.Datetime(string='Fecha Programada', index=True, required=True,
                                     states={'done': [('readonly', False)], 'cancel': [('readonly', False)]},
                                     help="Tiempo programado para que se procese la primera parte del envío. "
                                          "Configurar manualmente una fecha establecerá el estado en 'confirmado'.")
    date_done = fields.Datetime(string='Fecha Efectiva', index=True, help="Fecha de finalización de la transferencia.",
                                readonly=False)
    date_deadline = fields.Datetime(string='Fecha Límite', index=True,
                                    help="Promesa de fecha al cliente en el documento de nivel superior (orden de "
                                         "venta/de compra)",
                                    readonly=False)

    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'done':
            self.date_done = fields.Datetime.now()
