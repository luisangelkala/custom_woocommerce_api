# Contexto del Proyecto: Custom WooCommerce API (Odoo 17)

## 1. Descripción del Negocio
Este módulo gestiona una empresa de **Leasing/Renting (Alquiler Financiero)**.
- **Modelo de Venta:** No vendemos productos a precio único. Vendemos contratos basados en **Cuotas Mensuales** (`price_quote`).
- **Origen de Datos:** Los productos se crean y actualizan desde WooCommerce vía API REST.

## 2. Reglas Técnicas Críticas (DO NOT TOUCH)
### A. Cálculo de Cuotas (`models/order.py`)
- La cuota mensual (`price_quote`) se calcula automáticamente:
  - `Base = Precio Lista * 2.2`
  - `Fórmula Financiera = (Base + (Base * Tasa * Plazo)) / Plazo`
- **Importante:** El descuento (`discount_price`) **NO** reduce la cuota base. Se aplica después, afectando solo al subtotal a pagar.

### B. Impuestos Híbridos
- Se usa un parche en `_convert_to_tax_base_line_dict` para que Odoo calcule impuestos sobre la cuota mensual real y no sobre el precio de lista del activo.

### C. API (`controllers/product_api.py`)
- La estructura de respuesta JSON (`status`, `message`) debe mantenerse intacta para no romper la conexión con el plugin de WordPress.

## 3. Estructura de Archivos Clave
- `models/order.py`: Lógica financiera (`_compute_price_quote`) y gestión de líneas de pedido.
- `controllers/product_api.py`: Endpoints `POST`, `PUT`, `DELETE` para productos.
- `views/portal_saleorder_custom.xml`: Vista del cliente. Oculta precios unitarios y muestra "Loyer Mensuel" (Alquiler Mensual).

## 4. Instrucciones para el Asistente
- Actúa como experto en Odoo 17 Community.
- Al sugerir código, verifica no romper la lógica de cuotas financieras.
- Si se pide modificar la API, asegurar retrocompatibilidad con los campos existentes (`sku`, `sales_price`, `discount`).
- **Estilo de Respuesta:** Proporciona el código en formato `diff` siempre que sea posible.
- **Alcance:** Solo modifica el código estrictamente necesario para el requerimiento.
- **Explicación:** Explica brevemente el porqué de los cambios técnicos.