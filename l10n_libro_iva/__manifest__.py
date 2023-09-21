# -*- coding: utf-8 -*-
{
    'name': "Libros de Iva y Ajustes en fechas",

    'summary': """
        Módulo para desplegar en vista libros de compra y venta""",

    'description': """
        Módulo para desplegar en vista libros de compra y venta en El Salvador 
    """,

    'author': "Rocketters",
    'website': "https://rocketters.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'purchase', 'report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/move_type_data.xml',
        # 'views/actions.xml',
        'views/compra_libro_ccf.xml',
        'views/libro_venta_ccf.xml',
        'views/libro_venta_cf.xml',
        'wizard/export_book_view.xml',
        'views/menus.xml',
        'views/account_move_line.xml',
        'views/res.partner_view.xml',
        'views/account_journal_view.xml',
        # 'report/template_libro_base.xml',
        'report/template_libro_compra.xml',
        # 'views/views.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
