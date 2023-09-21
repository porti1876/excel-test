from odoo import http
from odoo.http import request

class PurchaseReport(http.Controller):
    @http.route('/purchase/report', type='http', auth='user')
    def purchase_report(self):
        # Código para generar el informe de compra aquí
        return request.render('purchase_report.template', {})
