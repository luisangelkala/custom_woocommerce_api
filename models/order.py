# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.float_utils import float_round
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Auto monthly (computed from list price and palier)
    price_quote = fields.Float(
        string="Auto Monthly Quote",
        compute="_compute_price_quote",
        store=True
    )

    # UI-visible mirror; only synced from auto if no manual value
    display_price_quote = fields.Float(
        string="Auto Monthly Quote (Visible)",
        readonly=False
    )

    # Optional: user can type a manual monthly value in the UI
    manual_price_quote = fields.Float(
        string="Manual Monthly Quote",
        help="Overrides the automatically calculated monthly quote if set."
    )

    include_full_service_warranty = fields.Boolean(
        string="Include Full Service Warranty",
        default=False
    )

    # Final monthly after applying manual/auto + warranty
    effective_price_quote = fields.Float(
        string="Monthly Quote (Final)",
        compute="_compute_effective_price_quote",
        store=True
    )

    # Subtotal = monthly final * qty (stored)
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price_subtotal_custom',
        store=True,
        currency_field='currency_id'
    )

    discount_price = fields.Float(string='Discount (%)', default=0.0, store=True)

    # ---------- ONCHANGE (Sincronización WP) ----------
    @api.onchange('product_id')
    def _onchange_product_id_apply_brand_discount(self):
        for line in self:
            if line.product_id:
                # Copiamos el descuento de WP al campo de la línea
                line.discount_price = line.product_id.x_brand_discount or 0.0

    # ---------- COMPUTES ----------

    @api.depends(
        'price_unit',
        'include_full_service_warranty',
        'order_id.full_service_warranty_percentage',
        'order_id.installments',
        # Quitamos discount_price de aquí porque el descuento ya no afecta la cuota bruta
    )
    def _compute_price_quote(self):
        for line in self:
            # 1. Obtenemos el precio base del activo
            total = (line.price_unit or 0.0) * 2.2
            months = int(line.order_id.installments or 24)
            rate = 0.05 / 12.0

            try:
                # 2. Calculamos la Cuota Financiera Base
                base_quote = (total + (total * rate * months)) / months
                
                # 3. Sumamos garantía si aplica
                if line.include_full_service_warranty and line.order_id.full_service_warranty_percentage:
                    base_quote += base_quote * (line.order_id.full_service_warranty_percentage / 100.0)
                
                # --- CAMBIO IMPORTANTE: YA NO RESTAMOS EL DESCUENTO AQUÍ ---
                # Queremos que 'price_quote' sea el valor BRUTO de la cuota.
                # El descuento se aplicará visualmente en el subtotal.
                
                final = float_round(base_quote, precision_digits=2)
                
                line.price_quote = final
                
                if not line.manual_price_quote:
                    line.display_price_quote = final

            except Exception as e:
                _logger.error(f"Error computing price_quote for line {line.id}: {e}")
                line.price_quote = 0.0
                if not line.manual_price_quote:
                    line.display_price_quote = 0.0

    @api.depends(
        'manual_price_quote',
        'price_quote',
        'include_full_service_warranty',
        'order_id.full_service_warranty_percentage',
        'order_id.installments'
    )
    def _compute_effective_price_quote(self):
        for line in self:
            # Esto ahora representa la CUOTA BRUTA (antes de descuento)
            base = line.manual_price_quote or line.price_quote or 0.0
            if line.include_full_service_warranty and line.order_id.full_service_warranty_percentage:
                base += base * (line.order_id.full_service_warranty_percentage / 100.0)
            line.effective_price_quote = float_round(base, precision_digits=2)

    @api.depends('effective_price_quote', 'product_uom_qty', 'currency_id', 'price_unit', 'price_tax', 'discount_price')
    def _compute_price_subtotal_custom(self):
        for line in self:
            # A) Determinamos el PRECIO UNITARIO BASE
            # Si hay cuota calculada (Leasing), usamos la cuota bruta.
            # Si no (Venta WP simple), usamos el precio de lista.
            if line.effective_price_quote and line.effective_price_quote > 0.0:
                unit_price_to_use = line.effective_price_quote
            else:
                unit_price_to_use = line.price_unit

            # B) Aplicamos el DESCUENTO matemáticamente aquí
            discount_factor = 1.0 - ((line.discount_price or 0.0) / 100.0)
            
            # C) Calculamos el subtotal (Precio * FactorDescuento * Cantidad)
            subtotal = (unit_price_to_use or 0.0) * discount_factor * (line.product_uom_qty or 0.0)
            
            line.price_subtotal = float_round(subtotal, precision_rounding=line.currency_id.rounding)
            line.price_total = line.price_subtotal + (line.price_tax or 0.0)

    @api.depends('effective_price_quote', 'product_uom_qty', 'tax_id', 'price_unit', 'discount_price')
    def _compute_tax_id(self):
        for line in self:
            # Misma lógica híbrida para impuestos
            if line.effective_price_quote and line.effective_price_quote > 0.0:
                unit_price_to_use = line.effective_price_quote
            else:
                unit_price_to_use = line.price_unit

            # Odoo compute_all ya sabe manejar descuentos si se los pasamos,
            # pero como calculamos manual, pasamos el precio con descuento ya aplicado
            # o dejamos que Odoo maneje el descuento (preferible pasar precio base y descuento).
            
            # Opción robusta: Pasamos el precio base y le decimos a Odoo el % de descuento
            taxes = line.tax_id.compute_all(
                unit_price_to_use or 0.0,
                currency=line.order_id.currency_id,
                quantity=line.product_uom_qty or 0.0,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
                handle_price_include=False,
                discount=line.discount_price # <--- Pasamos el descuento al motor de impuestos
            )
            line.price_tax = float_round(
                taxes['total_included'] - taxes['total_excluded'],
                precision_rounding=line.currency_id.rounding
            )

    # ---------- HOOK DEL MOTOR DE IMPUESTOS (HÍBRIDO) ----------
    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        res = super()._convert_to_tax_base_line_dict()
        
        # Le decimos al sistema de reportes cuál es el precio unitario real (Bruto)
        if self.effective_price_quote and self.effective_price_quote > 0.0:
            res['price_unit'] = self.effective_price_quote
        
        # Nos aseguramos de que el sistema sepa que hay un descuento
        res['discount'] = self.discount_price

        return res

    # ---------- ONCHANGES ----------
    @api.onchange('manual_price_quote')
    def _onchange_manual_quote(self):
        for line in self:
            if line.manual_price_quote:
                line.include_full_service_warranty = False

    @api.onchange('product_uom_qty', 'display_price_quote', 'discount_price')
    def _onchange_qty_or_quote(self):
        self._compute_effective_price_quote()
        self._compute_price_subtotal_custom()

    @api.onchange('include_full_service_warranty', 'order_id.full_service_warranty_percentage')
    def _onchange_warranty_toggle(self):
        for line in self:
            if not line.manual_price_quote:
                line._compute_price_quote()
                line._compute_effective_price_quote()
                line._compute_price_subtotal_custom()

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'include_full_service_warranty': self.include_full_service_warranty,
            'price_unit': (self.product_id.list_price or 0.0) * 2.2, 
            'product_list_price': self.product_id.list_price or 0.0,
            'tax_ids': [(6, 0, [])],
            'discount': self.discount_price # Pasamos el descuento a la factura también
        })
        return res