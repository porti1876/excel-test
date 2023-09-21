from odoo import fields, models, api


class AccountMoveVatBookSv(models.Model):
    _inherit = 'account.move'

    def open_wizard_vat_book(self):
        return self.env.ref('l10n_libro_iva.view_export_vat_book_sv').report_action(self)
