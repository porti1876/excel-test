from odoo import models, fields, api


class ResPartnerSujetoExcluido(models.Model):
    _inherit = "res.partner"

    is_sujeto_excluido = fields.Boolean(string="¿Es sujeto excluido?")
    is_inter_libro_compra = fields.Selection(string="¿Es un contacto para importación o internación?",
                                             help="Se seleccionará para el libro de compra de las facturas de este "
                                                  "contacto",
                                             selection=[('internacion', 'Internaciones'), ('importacion', 'Importaciones')])
    is_export_libro_cf = fields.Selection(string="¿Es un contacto para exportación?",
                                          help="Se seleccionará para el libro de ventas consumidor final que tipo de exportación es",
                                          selection=[('out_ca', 'Fuera De La Región Centroamericana'),
                                                     ('in_ca', 'Región Centroamericana'),
                                                     ('zona', 'Zona Franca')])



