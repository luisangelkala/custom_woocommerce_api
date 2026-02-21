# __manifest__.py
{
    'name': 'Custom WooCommerce API2',
    'version': '1.0',
    'category': 'Custom',
    'author': 'Tu Nombre',
    'description': 'Módulo para integrar WooCommerce con Odoo a través de una API personalizada.',
    'depends': ['base', 'web', 'sale', 'crm', 'contacts', 'account', 'portal'],  # AÑADIDO 'web', 'account' y 'portal'
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/financing_agency_menu.xml',
        'views/account_move_views.xml',
        'views/crm_quick_create_patch.xml',
        'views/create_lead_oportunity.xml',
        'views/report_saleorder_custom.xml',
        'views/portal_saleorder_custom.xml',
        'views/account_move_report_patch.xml',  # ESTE es para el PDF/print
        'views/portal_invoice_custom.xml',       # ESTE es para la vista web del portal
        'views/financing_agency_form_patch.xml',
        'views/account_move_form_patch.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
    ],
    'controllers': [
        'controllers/main.py',
        'controllers/product_api.py',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_woocommerce_api/static/src/js/kanban_quick_create_patch.js',
            'custom_woocommerce_api/static/src/js/crm_quick_create_redirect.js',
            'custom_woocommerce_api/static/src/css/custom_styles.css',
        ],
        'web.report_assets_common': [
            'custom_woocommerce_api/static/src/css/report_footer.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}