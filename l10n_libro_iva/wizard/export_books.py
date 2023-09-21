from odoo import api, fields, models
import datetime


class VatBookSvWizard(models.TransientModel):
    _name = 'export.vat.book.sv'
    _description = 'Wizard para generar libros de iva SV'

    select_book = fields.Selection(string="Libro a exportar",
                                   selection=[("ventas_ccf", "Libro de ventas Contribuyentes"),
                                              ("ventas_cf", "Libro de ventas Consumidor Final/Fex"),
                                              ("compra", "Libro de compras")], required=True)
    date_from = fields.Date(string="Fecha desde", default=fields.Date.context_today, required=True)
    date_to = fields.Date(string="Fecha hasta", default=fields.Date.context_today, required=True)
    company_id = fields.Many2one('res.company', string="Compañia", default=lambda self: self.env.company, readonly=True)
    vat_company = fields.Char(related="company_id.vat", string="NRC De empresa")
    nit_company = fields.Char(related="company_id.company_registry", string="NIT de empresa")
    journal_ids = fields.Many2many(
        'account.journal',
        string='Diarios para libros de iva',
        domain=[('book_type', '=', 'ccf')],
        default=lambda self: self.env['account.journal'].search([('book_type', '=', 'ccf')])
    )
    print_report_name = fields.Char(string="Print Report Name", compute="_compute_print_report_name")
# TODO: Dejar fecha como estaba de intervalo de date
    @api.depends('date_from', 'date_to', 'company_id')
    def _compute_print_report_name(self):
        for record in self:
            if record.date_from and record.date_to and record.company_id:
                record.print_report_name = "{}-{}-{}".format(record.date_from, record.date_to, record.company_id.name)
            else:
                record.print_report_name = "Libro de IVA"

    def open_selected_book(self):
        action = False
        view_id = False
        domain = []

        if self.select_book == 'ventas_ccf':
            domain = ['&', ('move_type', 'in', ['out_invoice', 'out_refund', 'entry']),
                      ('journal_id.book_type', '=', 'ccf'),
                      ('date', '>=', self.date_from),
                      ('date', '<=', self.date_to)]
            view_id = self.env.ref('l10n_libro_iva.view_libro_venta_vendor')
        elif self.select_book == 'ventas_cf':
            domain = ['&', ('move_type', 'in', ['out_invoice', 'out_refund']),
                      ('journal_id.book_type', '=', 'fcf'),
                      ('date', '>=', self.date_from),
                      ('date', '<=', self.date_to)]
            view_id = self.env.ref('l10n_libro_iva.view_libro_venta_cf')

        #     TODO: NO ACEPTA LA VARIABLE ""FINAL_DATE"" YA QUE ES VARIABLE CALCULADA, ENCONTRAR SOLUCION YA QUE TIENE
        #      QUE AGARRAR ESA VARIABLE POR LA FECHA
        elif self.select_book == 'compra':
            domain = [('move_type', 'in', ['in_invoice', 'entry', 'in_refund']),
                      ('state', '=', 'posted'),
                      ('journal_id.book_type', '=', 'compra'),
                      ('is_invoice_book', '=', True),
                      ('date', '>=', self.date_from),
                      ('date', '<=', self.date_to)]
            view_id = self.env.ref('l10n_libro_iva.view_libro_compra_proveedor')

        book_selection_labels = {
            'ventas_ccf': 'Libro de ventas Contribuyentes',
            'ventas_cf': 'Libro de ventas Consumidor Final/Fex',
            'compra': 'Libro de compras'
        }
        if view_id:
            name = book_selection_labels.get(self.select_book, self.select_book)
            action = {
                'name': f"{name} (Desde {self.date_from} Hasta {self.date_to})",
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree',
                'domain': domain,
                'context': {'default_move_type': 'out_invoice' if 'ventas' in self.select_book else 'in_invoice'},
                'view_id': view_id.id,
            }

        return action

    def action_print_compra_book(self):
        domain = []
        if self.select_book == 'ventas_ccf':
            domain = ['&', ('move_type', 'in', ['out_invoice', 'out_refund', 'entry']),
                      # ('journal_id.book_type', '=', 'ccf'),
                      ('date', '>=', self.date_from),
                      ('date', '<=', self.date_to)]
        elif self.select_book == 'ventas_cf':
            domain = ['&', ('move_type', 'in', ['out_invoice', 'out_refund']),
                      ('journal_id.book_type', '=', 'fcf'),
                      ('date', '>=', self.date_from),
                      ('date', '<=', self.date_to)]
        elif self.select_book == 'compra':
            domain = [('move_type', 'in', ['in_invoice', 'entry', 'in_refund']),
                      ('state', '=', 'posted'),
                      ('journal_id.book_type', '=', 'compra'),
                      ('is_invoice_book', '=', True),
                      ('date', '>=', self.date_from),
                      ('date', '<=', self.date_to)]


        account_moves_compra = self.env['account.move'].search_read(domain,
                                                                    ['journal_id','move_type', 'name','empty_field','name','date','ref', 'document_nrc',
                                                                     'partner_id','document_nit_dui','compras_exentas_internas',
                                                                    'compras_exentas_importacion','compras_exentas_internacional',
                                                                     'compras_gravadas_internas','compras_gravadas_importacion',
                                                                     'compras_gravadas_internacionales','iva_ccf',
                                                                     'amount_total_compras','anticipo_cuenta_percibido',
                                                                     'compras_retencion_terceros', 'compras_sujeto_excluido','final_date',

                                                                     'ventas_no_sujetas','ventas_exentas_ccf','ventas_gravadas_ccf','ventas_exentas_terceros',
                                                                     'ventas_gravadas_terceros','ventas_iva_terceros','retencion_fc','percepcion_ccf','total_ccf',

                                                                     'invoice_date','num_local_fc','num_caja','ventas_no_sujetas',
                                                                     'ventas_exentas_fc','ventas_gravadas_fc','ventas_exportaciones_fc',
                                                                     'percepcion_fc','total_fc',
                                                                     'ventas_cuenta_terceros','book_type_related','selection_location_related', 'location_fex'],
                                                                     order='name ASC')
        data = {
            'data': self.read([])[0],
            'account_moves_compra': account_moves_compra
        }
        report_template = 'l10n_libro_iva.report_libro_compra_sv'

        return self.env.ref(report_template).with_context(landscape=True).report_action(docids=None, data=data)



