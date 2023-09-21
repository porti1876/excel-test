from odoo import models, fields, api


class AccountJournalBook(models.Model):
    _inherit = "account.journal"

    book_type = fields.Selection(string="Libro de ventas CCF/FCF",
                                 selection=[('ccf', 'libro de ventas contribuyentes'),
                                            ('fcf', 'libro de ventas consumidor final/ fex'),
                                            ('compra', 'Libro de compras')])

    select_location = fields.Selection(string="Ubicación en libro", help="Seleccione para efectos "
                                                                            "de libro de ventas",
                                       selection=[('matriz', 'Casa Matriz'), ('tecla', 'Sucursal Santa Tecla'),
                                                  ('fex','Exportación')])

    percepcion_purchase_book = fields.Boolean(string="Iva Percibido Libro de compra",
                                              help="Seleccionar si es un diario de IVA percibido para libro de compra")
