from odoo import models, fields, api


class AccountMoveType(models.Model):
    _name = 'account.move.type'
    _description = 'Modelo para ver el tipo de movimiento de la compra(gravadas o exentas)'

    name = fields.Char(string="Tipo de movimiento")
    description = fields.Char(string="Descripción")