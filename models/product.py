# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campo para guardar el porcentaje de descuento que viene de WP
    # Este es el dato "maestro" que sincroniza el plugin.
    x_brand_discount = fields.Float(string='WP Brand Discount (%)', default=0.0)