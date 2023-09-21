# -*- coding: utf-8 -*-

from odoo import models, fields, api
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta

from odoo.addons.account.models.account_move import AccountMove


class AccountMoveContacts(models.Model):
    _inherit = 'account.move'

    document_nrc = fields.Char(string="NRC", related="partner_id.vat")
    document_nit_dui = fields.Char(string="NIT/DUI", compute="_compute_dui_nit")
    empty_field = fields.Char(string="N°")
    incremental_number = fields.Integer(string="Incremental Number")
    sequential_month = fields.Integer(string='Secuencia')
    # invoice_date_only = fields.Integer(compute='_compute_invoice_date_only')
    # invoice_day = fields.Integer(compute='_compute_invoice_day', store=True)
    ventas_cuenta_terceros = fields.Char(string="Ventas a cuentas a terceros")
    num_local_cf = fields.Char(string="Local", default="-")
    ventas_exentas_terceros = fields.Char(string="Exentas cuenta de terceros")
    ventas_gravadas_terceros = fields.Char(string="Exentas gravadas de terceros")
    ventas_iva_terceros = fields.Char(string="Iva Deb. Fiscal")
    iva_retenido = fields.Char(string="Iva retenido")
    iva_percibido = fields.Char(string="Iva percibido")
    compras_gravadas_internacionales = fields.Char(string="Compras gravadas Internacionales",
                                                   compute="_compute_compras_gravadas")
    compras_retencion_terceros = fields.Char(string="Retencion a terceros")


    # Campos libro de ventas contribuyentes.
    ventas_exentas_ccf = fields.Float(string="Ventas exentas", compute="_compute_ventas_ccf")
    ventas_gravadas_ccf = fields.Float(string="Ventas gravadas", compute="_compute_ventas_ccf")
    total_ccf = fields.Float(string="Total libro ccf", compute="_compute_total_ccf")
    partner_doc_liquidacion = fields.Selection(related="journal_id.book_type", string="Libro en AM")
    percepcion_ccf = fields.Float(string="Percepción CCF", compute="_compute_iva_percibido_ccf")

    @api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
    def _compute_iva_percibido_ccf(self):
        for move in self:
            if move.state == 'posted':
                total_amount = sum(move.invoice_line_ids.mapped('price_subtotal'))
                impuestos_1 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == 1)
                impuestos_2 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == 2)
                if impuestos_1:
                    anticipo_amount = total_amount * 0.01
                    move.percepcion_ccf = anticipo_amount
                elif impuestos_2:
                    anticipo_amount = total_amount * 0.02
                    move.percepcion_ccf = anticipo_amount
                elif move.move_type == 'entry':
                    move.percepcion_ccf = move.amount_total_signed
                else:
                    move.percepcion_ccf = 0.0
            else:
                move.percepcion_ccf = 0.0

    @api.depends('amount_total_signed')
    def _compute_total_ccf(self):
        for move in self:
            if move.state == 'posted' and move.move_type in ['out_invoice', 'out_refund']:
                move.total_ccf = move.amount_total_signed
            else:
                move.total_ccf = 0.0

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.move_type_ids')
    def _compute_ventas_ccf(self):
        for move in self:
            if move.state == 'posted':
                exentas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'exentas')
                gravadas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'gravadas')
                partner_country = move.partner_id.country_id.code if move.partner_id.country_id else False
                if partner_country == 'SV' and exentas_lines:
                    move.ventas_exentas_ccf = sum(exentas_lines.mapped('price_subtotal'))
                    move.ventas_gravadas_ccf = 0.0
                elif partner_country == 'SV' and gravadas_lines:
                    move.ventas_gravadas_ccf = sum(gravadas_lines.mapped('price_subtotal'))
                    move.ventas_exentas_ccf = 0.0
                elif partner_country != 'SV':
                    move.ventas_exentas_ccf = sum(exentas_lines.mapped('price_subtotal'))
                    move.ventas_gravadas_ccf = 0.0

                # Verificar si move_type es igual a 'out_refund' para hacer que los valores sean negativos
                if move.move_type == 'out_refund':
                    move.ventas_exentas_ccf = -move.ventas_exentas_ccf
                    move.ventas_gravadas_ccf = -move.ventas_gravadas_ccf
            else:
                move.ventas_exentas_ccf = 0.0
                move.ventas_gravadas_ccf = 0.0



    # Campos libro de consumidor final venta
    num_local_fc = fields.Char(string="Local", default="-")
    num_caja = fields.Char(string="Núm de caja", default="-")
    ventas_no_sujetas = fields.Char(string="No Sujetas", default="-")
    ventas_exentas_fc = fields.Float(string="Ventas exentas", compute="_compute_ventas_fc")
    ventas_gravadas_fc = fields.Float(string="Ventas gravadas", compute="_compute_ventas_fc")
    ventas_exportaciones_fc = fields.Float(string="Exportaciones", compute="_compute_ventas_fc")
    retencion_fc = fields.Float(string="Retención", compute="_compute_iva_retenido_fc")
    percepcion_fc = fields.Float(string="Percepción", compute="_compute_iva_percibido_fc")
    total_fc = fields.Float(string="Total De libro de fc", compute="_compute_amount_total")
    origin_pur_name = fields.Char(string="Origin de compra")
    book_type_related = fields.Selection(related='journal_id.book_type', string="Libro de iva en diario")
    selection_location_related = fields.Selection(related='journal_id.select_location', string="Ubicación en libro")
    location_fex = fields.Selection(related="partner_id.is_export_libro_cf", string="Ubicación para exportaciones")


    @api.depends('amount_total_signed')
    def _compute_amount_total(self):
        for move in self:
            if move.state == 'posted':
                move.total_fc = move.amount_total_signed
            else:
                move.total_fc = 0.0    

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.move_type_ids', 'state')
    def _compute_ventas_fc(self):
        for move in self:
            if move.state == 'posted':  # Agregar condición del estado "posted"
                exentas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'exentas')
                gravadas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'gravadas')
                partner_country = move.partner_id.is_export_libro_cf if move.partner_id.is_export_libro_cf else False
                if not partner_country and exentas_lines:
                    move.ventas_exentas_fc = sum(exentas_lines.mapped('price_subtotal'))
                    move.ventas_gravadas_fc = 0.0
                    move.ventas_exportaciones_fc = 0.0
                elif not partner_country and gravadas_lines:
                    move.ventas_gravadas_fc = sum(gravadas_lines.mapped('price_subtotal')) * 1.13
                    move.ventas_exentas_fc = 0.0
                    move.ventas_exportaciones_fc = 0.0
                elif partner_country in ['out_ca', 'in_ca', 'zona'] :
                    move.ventas_exportaciones_fc = sum(exentas_lines.mapped('price_subtotal'))
                    move.ventas_gravadas_fc = 0.0
                    move.ventas_exentas_fc = 0.0
                else:
                    move.ventas_exportaciones_fc = 0.0
                    move.ventas_gravadas_fc = 0.0
                    move.ventas_exentas_fc = 0.0
            else:
                move.ventas_exportaciones_fc = 0.0
                move.ventas_gravadas_fc = 0.0
                move.ventas_exentas_fc = 0.0


    @api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
    def _compute_iva_retenido_fc(self):
        for move in self:
            if move.state == 'posted':
                total_amount = sum(move.invoice_line_ids.mapped('price_subtotal'))
                impuestos_1 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == -1)

                if impuestos_1:
                    anticipo_amount = total_amount * (-0.01)
                    move.retencion_fc = anticipo_amount
                else:
                    move.retencion_fc = 0.0
            else:
                move.retencion_fc = 0.0        

    @api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
    def _compute_iva_percibido_fc(self):
        for move in self:
            if move.state == 'posted':
                total_amount = sum(move.invoice_line_ids.mapped('price_subtotal'))
                impuestos_1 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == 1)
                impuestos_2 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == 2)
                if impuestos_1:
                    anticipo_amount = total_amount * 0.01
                    move.percepcion_fc = anticipo_amount
                elif impuestos_2:
                    anticipo_amount = total_amount * 0.02
                    move.percepcion_fc = anticipo_amount
                else:
                    move.percepcion_fc = 0.0
            else:
                move.percepcion_fc = 0.0        

    # Campos del libro de compras


    # Campos de totales gravados
    compras_gravadas_internas = fields.Float(string="Compras gravadas internas",
                                             compute='_compute_compras_gravadas')
    compras_gravadas_importacion = fields.Float(string="Compras gravadas importacion"
                                                , compute="_compute_compras_gravadas")
    compras_gravadas_internacionales = fields.Float(string="Compras gravadas Internacionales"
                                                    , compute="_compute_compras_gravadas")
    amount_total_compras = fields.Float(string="Monto total", compute="_compute_monto_total_compra")

    # Campos de totales exentoss
    compras_exentas_internas = fields.Float(string="Compras exentas internas", compute='_compute_compras_exentas')
    compras_exentas_internacional = fields.Float(string="Compras exentas internacionales",
                                                 compute='_compute_compras_exentas')
    compras_exentas_importacion = fields.Float(string="Compras exentas importación", compute='_compute_compras_exentas')

    # Iva percibido

    anticipo_cuenta_percibido = fields.Float(string="Anticipo a cuenta de IVA percibido",
                                             compute='_compute_anticipo_cuenta_percibido')

    # Compras sa sujeto excluido

    compras_sujeto_excluido = fields.Float(string="Compras a sujetos excluidos",
                                           compute="_compute_compra_sujeto_excluido")

    # IVA

    iva_ccf = fields.Float(string="IVA Crédito Fiscal", compute="_compute_iva_ccf")



    # Campos que sean 0 dependiendo el estado del mo movimiento:

    total_zero = fields.Float(default=0.0)

    # Campo de fecha que sea igual a la fecha de factura pero que se pueda modificar segun libro de compra


    is_late_date = fields.Boolean(string="¿Cambio de fecha para libro de IVA?", default=True)
    test_bool = fields.Boolean(string="Mantener fecha de factura en libro de compra", default=True,
                               help="Deseleccionar si quiere cambiar la fecha de la factura para libro de compra")

    libro_compra_fecha = fields.Date(
        string="Nueva fecha para libro de compra",
        help="Si se quiere que cambie en el libro de compra, esta fecha se tomará en cuenta",
    )


    final_date = fields.Date(string="Fecha final del libro de compra", compute="_compute_fecha_final")

    is_invoice_book = fields.Boolean(string="¿Aparece en libro de compra?", default=True,
                                     help="Si esta activado la factura aparecerá en libro de compras, si esta desactivado "
                                          "no aparecerá")

    percepcion_related = fields.Boolean(related="journal_id.percepcion_purchase_book",
                                        string="Campo relacionado de diario percepción en libro de compra")


    @api.depends('invoice_date')
    def _compute_fecha_final(self):
        for rec in self:
            if not rec.test_bool:
                rec.final_date = rec.libro_compra_fecha
            else:
                rec.final_date = rec.invoice_date or rec.date
    #
    # @api.onchange('is_late_date')
    # def _onchange_is_late_date(self):
    #     if self.is_late_date:
    #         self.final_date = self.libro_compra_fecha
    #     else:
    #         self.final_date = self.invoice_date


    @api.depends('amount_total')
    def _compute_monto_total_compra(self):
        for rec in self:
            if rec.partner_id.is_sujeto_excluido == True:
                rec.amount_total_compras = 0.0
            elif rec.move_type == 'entry':
                rec.amount_total_compras = 0.0
            elif rec.move_type == 'in_refund':
                rec.amount_total_compras = -rec.amount_total
            else:
                rec.amount_total_compras = rec.amount_total


    @api.depends('invoice_line_ids.tax_ids.amount')
    def _compute_iva_ccf(self):
        for move in self:
            if move.state == 'posted':
                gravadas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'gravadas')
                tax_13 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == 13)
                total_amount = sum(move.invoice_line_ids.mapped('price_subtotal'))
                total_gravadas = sum(gravadas_lines.mapped('price_subtotal'))
                if tax_13 and total_gravadas != 0:
                    iva = total_gravadas * 0.13
                    move.iva_ccf = iva
                elif tax_13 and total_gravadas == 0:
                    iva = total_amount * 0.13
                    move.iva_ccf = iva
                else:
                    move.iva_ccf = 0.0

                # Verificar si move_type es igual a 'out_refund' para hacer que el IVA sea negativo
                if move.move_type == 'out_refund':
                    move.iva_ccf = -move.iva_ccf
                # Verificar si move_type es igual a 'in_refund' para hacer que el IVA sea negativo
                elif move.move_type == 'in_refund':
                    move.iva_ccf = -move.iva_ccf
            else:
                move.iva_ccf = 0.0

    @api.depends('partner_id.document_dui', 'partner_id.nit_res_partner')
    def _compute_dui_nit(self):
        for move in self:
            if move.partner_id.document_dui:
                move.document_nit_dui = move.partner_id.document_dui
            elif move.partner_id.nit_res_partner:
                move.document_nit_dui = move.partner_id.nit_res_partner
            else:
                move.document_nit_dui = '-'

    @api.depends('invoice_line_ids.tax_ids', 'invoice_line_ids.price_subtotal')
    def _compute_anticipo_cuenta_percibido(self):
        for move in self:
            if move.state == 'posted':
                total_amount = sum(move.invoice_line_ids.mapped('price_subtotal'))
                impuestos_1 = move.invoice_line_ids.mapped('tax_ids').filtered(lambda tax: tax.amount == 1)

                if impuestos_1:
                    anticipo_amount = total_amount * 0.01
                    move.anticipo_cuenta_percibido = anticipo_amount
                elif move.move_type == 'entry':
                    move.anticipo_cuenta_percibido = move.amount_total_signed
                else:
                    move.anticipo_cuenta_percibido = 0.0

            else:
                move.anticipo_cuenta_percibido = 0.0


    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.move_type_ids', 'partner_id.is_sujeto_excluido')
    def _compute_compras_exentas(self):
        for move in self:
            exentas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'exentas')
            partner_country = move.partner_id.country_id.code if move.partner_id.country_id else False
            if partner_country == 'SV' and not move.partner_id.is_sujeto_excluido:
                move.compras_exentas_internas = sum(exentas_lines.mapped('price_subtotal'))
                move.compras_exentas_internacional = 0.0
                move.compras_exentas_importacion = 0.0
            elif partner_country in ['PA', 'CR', 'GT', 'HN', 'NI']:
                move.compras_exentas_internas = 0.0
                move.compras_exentas_importacion = 0.0
                move.compras_exentas_internacional = sum(exentas_lines.mapped('price_subtotal'))
            elif partner_country not in ['PA', 'CR', 'GT', 'HN', 'NI', 'SV']:
                move.compras_exentas_internas = 0.0
                move.compras_exentas_internacional = 0.0
                move.compras_exentas_importacion = sum(exentas_lines.mapped('price_subtotal'))
            else:
                move.compras_exentas_internas = 0.0
                move.compras_exentas_internacional = 0.0
                move.compras_exentas_importacion = 0.0

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.move_type_ids')
    def _compute_compras_gravadas(self):
        for move in self:
            gravadas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'gravadas')
            partner_country = move.partner_id.is_inter_libro_compra if move.partner_id else False
            if move.move_type == 'in_invoice':
                if partner_country == False:
                    move.compras_gravadas_internas = sum(gravadas_lines.mapped('price_subtotal'))
                    move.compras_gravadas_internacionales = 0.0
                    move.compras_gravadas_importacion = 0.0
                elif partner_country == 'internacion':
                    move.compras_gravadas_internas = 0.0
                    move.compras_gravadas_importacion = 0.0
                    move.compras_gravadas_internacionales = sum(gravadas_lines.mapped('price_subtotal'))
                else:
                    move.compras_gravadas_internas = 0.0
                    move.compras_gravadas_internacionales = 0.0
                    move.compras_gravadas_importacion = sum(gravadas_lines.mapped('price_subtotal'))

                if move.partner_id.is_sujeto_excluido == True:
                    move.compras_gravadas_internas = 0.0
                    move.compras_gravadas_internacionales = 0.0
                    move.compras_gravadas_importacion = 0.0

            elif move.move_type == 'in_refund':
                if partner_country == False:
                    move.compras_gravadas_internas = -sum(gravadas_lines.mapped('price_subtotal'))
                    move.compras_gravadas_internacionales = 0.0
                    move.compras_gravadas_importacion = 0.0
                elif partner_country == 'internacion':
                    move.compras_gravadas_internas = 0.0
                    move.compras_gravadas_importacion = 0.0
                    move.compras_gravadas_internacionales = -sum(gravadas_lines.mapped('price_subtotal'))
                else:
                    move.compras_gravadas_internas = 0.0
                    move.compras_gravadas_internacionales = 0.0
                    move.compras_gravadas_importacion = -sum(gravadas_lines.mapped('price_subtotal'))

                if move.partner_id.is_sujeto_excluido == True:
                    move.compras_gravadas_internas = 0.0
                    move.compras_gravadas_internacionales = 0.0
                    move.compras_gravadas_importacion = 0.0

            elif move.move_type == 'entry':
                move.compras_gravadas_internas = 0.0
                move.compras_gravadas_internacionales = 0.0
                move.compras_gravadas_importacion = 0.0


    @api.depends('partner_id.is_sujeto_excluido', 'invoice_line_ids.price_subtotal')
    def _compute_compra_sujeto_excluido(self):
        for move in self:
            total_amount = sum(move.invoice_line_ids.mapped('price_subtotal'))
            is_sujeto = move.partner_id.is_sujeto_excluido
            if is_sujeto:
                move.compras_sujeto_excluido = total_amount
                move.compras_exentas_internacional = 0.0
                move.compras_exentas_importacion = 0.0
                move.compras_exentas_internas = 0.0
            else:
                move.compras_sujeto_excluido = 0.00



class AccountMoveContacts(models.Model):
    _inherit = 'account.move.line'

    move_type_ids = fields.Selection(
        string="(Gravadas/Exentas)",
        selection=[('gravadas', 'Gravadas'), ('exentas', 'Exentas')],
        default='gravadas'
    )
    # user_move_type_ids = fields.Selection(
    #     string="(Gravadas/Exentas)",
    #     selection=[('gravadas', 'Gravadas'), ('exentas', 'Exentas')],
    #     default='gravadas'
    # )
    #
    # @api.depends('partner_id', 'user_move_type_ids')
    # def _compute_move_type_ids(self):
    #     for move in self:
    #         if move.partner_id.country_id.code != 'SV':
    #             move.move_type_ids = 'exentas'
    #         else:
    #             move.move_type_ids = move.user_move_type_ids

    @api.depends('move_id.invoice_line_ids.price_subtotal', 'move_id.invoice_line_ids.move_type_ids')
    def _compute_compras_exentas(self):
        for move_line in self:
            move = move_line.move_id
            exentas_lines = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'exentas')
            partner_country = move.partner_id.country_id
            if partner_country == move.env.ref('base.sv'):
                move.compras_exentas_internas = sum(exentas_lines.mapped('price_subtotal'))
            elif partner_country in move.env.ref('base.pa') + move.env.ref('base.cr') + move.env.ref(
                    'base.gt') + move.env.ref('base.hn') + move.env.ref('base.ni'):
                move.compras_exentas_internacional = sum(exentas_lines.mapped('price_subtotal'))
            else:
                move.compras_exentas_importacion = sum(exentas_lines.mapped('price_subtotal'))

    @api.depends('move_id.invoice_line_ids.price_subtotal', 'move_id.invoice_line_ids.move_type_ids')
    def _compute_compras_gravadas_internas(self):
        for move_line in self:
            move = move_line.move_id
            gravadas_lines: account.move.line = move.invoice_line_ids.filtered(lambda line: line.move_type_ids == 'gravadas')
            partner_country = move.partner_id.country_id
            if partner_country == move.env.ref('base.sv'):
                move.compras_gravadas_internas = sum(gravadas_lines.mapped('price_subtotal'))
            elif partner_country in move.env.ref('base.pa') + move.env.ref('base.cr') + move.env.ref(
                    'base.gt') + move.env.ref('base.hn') + move.env.ref('base.ni'):
                move.compras_gravadas_importacion = sum(gravadas_lines.mapped('price_subtotal'))
            else:
                move.compras_gravadas_internacionales = sum(gravadas_lines.mapped('price_subtotal'))

# Clase para generar libro de compras de contribuyentes
class PartnerXlsx(models.AbstractModel):
    _name = 'report.l10n_libro_iva.report_test_libro_compra'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, move):
        sheet = workbook.add_worksheet('Libro de Compra')

        # Establecer estilo para la sección de la empresa
        header_format_company = workbook.add_format(
            {'align': 'center', 'bold': True, 'border': 1, 'bg_color': '#CCE5FF'})
        cell_format = workbook.add_format({'border': 1})
        info_format = workbook.add_format({'align': 'center'})
        total_format = workbook.add_format({'num_format': '$ #,##0.00', 'align': 'center'})
        # Agregar información de la empresa en la tabla
        sheet.write('A1', 'Nombre de la Empresa', header_format_company)
        sheet.write('A2', 'Dirección de la Empresa', header_format_company)
        sheet.write('A3', 'Teléfono de la Empresa', header_format_company)
        sheet.write('A4', 'NRC de la Empresa', header_format_company)
        sheet.write('C1', 'Libro de compra de contribuyentes', header_format_company)

        sheet.write('B1', move.company_id.name, cell_format)
        sheet.write('B2', move.company_id.street, cell_format)
        sheet.write('B3', move.company_id.phone, cell_format)
        sheet.write('B4', move.company_id.vat, cell_format)

        # Ajustar ancho de columnas
        sheet.set_column('A1:C4', 35)  # Ajusta el ancho de las columnas A a S según tus necesidades
        sheet.set_column('A7:Q7', 30)  # Ajusta el ancho de las columnas A a S según tus necesidades

        # Agregar encabezados de las columnas
        header_format = workbook.add_format({'bg_color': '#8CB5E2', 'align': 'center', 'bold': True})
        sheet.write(6, 0, 'Número', header_format)
        sheet.write(6, 1, 'Fecha de factura', header_format)
        sheet.write(6, 2, 'Número del documento', header_format)
        sheet.write(6, 3, 'NRC', header_format)
        sheet.write(6, 4, 'NIT/DUI', header_format)
        sheet.write(6, 5, 'Nombre', header_format)
        sheet.write(6, 6, 'Compras exentas locales', header_format)
        sheet.write(6, 7, 'Compras exentas importaciones', header_format)
        sheet.write(6, 8, 'Compras exentas internaciones', header_format)
        sheet.write(6, 9, 'Compras gravadas locales', header_format)
        sheet.write(6, 10, 'Compras gravadas importaciones', header_format)
        sheet.write(6, 11, 'Compras gravadas internaciones', header_format)
        sheet.write(6, 12, 'IVA crédito fiscal', header_format)
        sheet.write(6, 13, 'Total Compras', header_format)
        sheet.write(6, 14, 'Iva percibido', header_format)
        sheet.write(6, 15, 'Retención a terceros', header_format)
        sheet.write(6, 16, 'Compras a sujetos excluidos', header_format)
        # Agrega más encabezados según tus campos

        # Escribir datos de cada registro en el archivo Excel
        for index, obj in enumerate(move):
            # Obtener la fecha en formato de fecha legible
            libro_compra_fecha = obj.libro_compra_fecha
            invoice_date_str = libro_compra_fecha.strftime('%d/%m/%Y') if libro_compra_fecha else ''

            row = index + 7

            sheet.write(row, 0, obj.empty_field or '', info_format)
            sheet.write(row, 1, invoice_date_str or '-', info_format)
            sheet.write(row, 2, obj.name or '', info_format)
            sheet.write(row, 3, obj.document_nrc or '-', info_format)
            sheet.write(row, 4, obj.document_nit_dui or obj.partner_id.document_dui or '-', info_format)
            sheet.write(row, 5, obj.partner_id.name or '-', info_format)
            sheet.write(row, 6, obj.compras_exentas_internas or '$-', total_format)
            sheet.write(row, 7, obj.compras_exentas_importacion or '$-', total_format)
            sheet.write(row, 8, obj.compras_exentas_internacional or '$-', total_format)
            sheet.write(row, 9, obj.compras_gravadas_internas or '$ -', total_format)
            sheet.write(row, 10, obj.compras_gravadas_importacion or '$ -', total_format)
            sheet.write(row, 11, obj.compras_gravadas_internacionales or '$ -', total_format)
            sheet.write(row, 12, obj.iva_ccf or '$ -', total_format)
            sheet.write(row, 13, obj.amount_total or '$ -', total_format)
            sheet.write(row, 14, obj.anticipo_cuenta_percibido or '$ -', total_format)
            sheet.write(row, 15, obj.compras_retencion_terceros or '-', total_format)
            sheet.write(row, 16, obj.compras_sujeto_excluido or '-', total_format)

            # Agrega más campos según tus necesidades

        # Retorna el archivo Excel generado
        return workbook

# Clase para generar libro de ventas de contribuyentes
class PartnerXlsxCcf(models.AbstractModel):
    _name = 'report.l10n_libro_iva.report_test_libro_venta_ccf'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, move):
        sheet = workbook.add_worksheet('Libro de Venta Contribuyentes')

        # Establecer estilo para la sección de la empresa
        header_format_company = workbook.add_format(
            {'align': 'center', 'bold': True, 'border': 1, 'bg_color': '#CCE5FF'})
        cell_format = workbook.add_format({'border': 1})
        info_format = workbook.add_format({'align': 'center'})
        total_format = workbook.add_format({'num_format': '$ #,##0.00', 'align': 'center'})
        # Agregar información de la empresa en la tabla
        sheet.write('A1', 'Nombre de la Empresa', header_format_company)
        sheet.write('A2', 'Dirección de la Empresa', header_format_company)
        sheet.write('A3', 'Teléfono de la Empresa', header_format_company)
        sheet.write('A4', 'NRC de la Empresa', header_format_company)
        sheet.write('C1', 'Libro de ventas de contribuyentes', header_format_company)

        sheet.write('B1', move.company_id.name, cell_format)
        sheet.write('B2', move.company_id.street, cell_format)
        sheet.write('B3', move.company_id.phone, cell_format)
        sheet.write('B4', move.company_id.vat, cell_format)

        # Ajustar ancho de columnas
        sheet.set_column('A1:C4', 35)  # Ajusta el ancho de las columnas A a S según tus necesidades
        sheet.set_column('A7:Q7', 30)  # Ajusta el ancho de las columnas A a S según tus necesidades

        # Agregar encabezados de las columnas
        header_format = workbook.add_format({'bg_color': '#8CB5E2', 'align': 'center', 'bold': True})
        sheet.write(6, 0, 'Número', header_format)
        sheet.write(6, 1, 'Número del documento', header_format)
        sheet.write(6, 2, 'Fecha de emisión', header_format)
        sheet.write(6, 3, 'Nombre', header_format)
        sheet.write(6, 4, 'NRC', header_format)
        sheet.write(6, 5, 'Ventas no sujetas', header_format)
        sheet.write(6, 6, 'Ventas exentas', header_format)
        sheet.write(6, 7, 'Ventas gravadas', header_format)
        sheet.write(6, 8, 'Iva Deb. Fiscal', header_format)
        sheet.write(6, 9, 'Ventas exentas 3ros', header_format)
        sheet.write(6, 10, 'Ventas gravadas 3ros', header_format)
        sheet.write(6, 11, 'Iva Deb. Fiscal 3ros', header_format)
        sheet.write(6, 12, 'Iva retenido', header_format)
        sheet.write(6, 13, 'Iva percibido', header_format)
        sheet.write(6, 14, 'Venta total', header_format)
        # Agrega más encabezados según tus campos

        # Escribir datos de cada registro en el archivo Excel
        for index, obj in enumerate(move):
            # Obtener la fecha en formato de fecha legible
            invoice_date = obj.invoice_date
            invoice_date_str = invoice_date.strftime('%d/%m/%Y') if invoice_date else ''

            row = index + 7

            sheet.write(row, 0, obj.empty_field or '', info_format)
            sheet.write(row, 1, obj.name or '-', info_format)
            sheet.write(row, 2, invoice_date_str or '', info_format)
            sheet.write(row, 3, obj.partner_id.name or '-', info_format)
            sheet.write(row, 4, obj.document_nrc or '-', info_format)
            sheet.write(row, 5, obj.ventas_no_sujetas or '$-', info_format)
            sheet.write(row, 6, obj.ventas_exentas_ccf or '$-', total_format)
            sheet.write(row, 7, obj.ventas_gravadas_ccf or '$-', total_format)
            sheet.write(row, 8, obj.iva_ccf or '$-', total_format)
            sheet.write(row, 9, obj.ventas_exentas_terceros or '$ -', total_format)
            sheet.write(row, 10, obj.ventas_gravadas_terceros or '$ -', total_format)
            sheet.write(row, 11, obj.ventas_iva_terceros or '$ -', total_format)
            sheet.write(row, 12, obj.retencion_fc or '$ -', total_format)
            sheet.write(row, 13, obj.percepcion_fc or '$ -', total_format)
            sheet.write(row, 14, obj.total_ccf or '$ -', total_format)


            # Agrega más campos según tus necesidades

        # Retorna el archivo Excel generado
        return workbook

# Clase para generar libro de ventas consumidor final.

class PartnerXlsxFc(models.AbstractModel):
    _name = 'report.l10n_libro_iva.report_test_libro_venta_fc'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, move):
        sheet = workbook.add_worksheet('Libro de Venta Consumidor Final')

        # Establecer estilo para la sección de la empresa
        header_format_company = workbook.add_format(
            {'align': 'center', 'bold': True, 'border': 1, 'bg_color': '#CCE5FF'})
        cell_format = workbook.add_format({'border': 1})
        info_format = workbook.add_format({'align': 'center'})
        total_format = workbook.add_format({'num_format': '$ #,##0.00', 'align': 'center'})
        # Agregar información de la empresa en la tabla
        sheet.write('A1', 'Nombre de la Empresa', header_format_company)
        sheet.write('A2', 'Dirección de la Empresa', header_format_company)
        sheet.write('A3', 'Teléfono de la Empresa', header_format_company)
        sheet.write('A4', 'NRC de la Empresa', header_format_company)
        sheet.write('C1', 'Libro de ventas de consumidor final', header_format_company)

        sheet.write('B1', move.company_id.name, cell_format)
        sheet.write('B2', move.company_id.street, cell_format)
        sheet.write('B3', move.company_id.phone, cell_format)
        sheet.write('B4', move.company_id.vat, cell_format)

        # Ajustar ancho de columnas
        sheet.set_column('A1:C4', 35)  # Ajusta el ancho de las columnas A a S según tus necesidades
        sheet.set_column('A7:Q7', 30)  # Ajusta el ancho de las columnas A a S según tus necesidades

        # Agregar encabezados de las columnas
        header_format = workbook.add_format({'bg_color': '#8CB5E2', 'align': 'center', 'bold': True})
        sheet.write(6, 0, 'Fecha', header_format)
        sheet.write(6, 1, 'Número del documento', header_format)
        sheet.write(6, 2, 'Local', header_format)
        sheet.write(6, 3, 'Caja', header_format)
        sheet.write(6, 4, 'No Sujetas', header_format)
        sheet.write(6, 5, 'Ventas exentas', header_format)
        sheet.write(6, 6, 'Ventas gravadas', header_format)
        sheet.write(6, 7, 'Exportaciones', header_format)
        sheet.write(6, 8, 'Retención', header_format)
        sheet.write(6, 9, 'Percepción', header_format)
        sheet.write(6, 10, 'Total', header_format)
        sheet.write(6, 11, 'Venta a cuenta de terceros', header_format)
        # Agrega más encabezados según tus campos

        # Escribir datos de cada registro en el archivo Excel
        for index, obj in enumerate(move):
            # Obtener la fecha en formato de fecha legible
            invoice_date = obj.invoice_date
            invoice_date_str = invoice_date.strftime('%d/%m/%Y') if invoice_date else ''

            row = index + 7

            sheet.write(row, 0, invoice_date_str or '', info_format)
            sheet.write(row, 1, obj.name or '-', info_format)
            sheet.write(row, 2, obj.num_local_fc or '-', info_format)
            sheet.write(row, 3, obj.num_caja or '-', info_format)
            sheet.write(row, 4, obj.ventas_no_sujetas or '$-', info_format)
            sheet.write(row, 5, obj.ventas_exentas_fc or '$-', total_format)
            sheet.write(row, 6, obj.ventas_gravadas_fc or '$-', total_format)
            sheet.write(row, 7, obj.ventas_exportaciones_fc or '$-', total_format)
            sheet.write(row, 8, obj.retencion_fc or '$-', total_format)
            sheet.write(row, 9, obj.percepcion_fc or '$ -', total_format)
            sheet.write(row, 10, obj.total_fc or '$ -', total_format)
            sheet.write(row, 11, obj.ventas_cuenta_terceros or '$ -', total_format)

            # Agrega más campos según tus necesidades

        # Retorna el archivo Excel generado
        return workbook

