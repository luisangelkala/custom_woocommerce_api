from odoo import http
from odoo.http import request
import json

class ProductAPIController(http.Controller):

    @http.route('/api/product', auth='user', methods=['POST'], type='json', csrf=False)
    def create_product(self, **post):
        try:
            data = json.loads(request.httprequest.data)
            
            name = data.get('name')
            if not name:
                return {"status": "error", "message": "Missing required field: name"}

            sku = data.get('sku')
            sales_price = data.get('sales_price')
            description = data.get('description')
            discount = data.get('discount') # Nuevo campo

            if sku:
                product = request.env['product.product'].sudo().search([('default_code', '=', sku)], limit=1)
                if product:
                    return {"status": "error", "message": f"Product with SKU {sku} already exists"}

            new_product = request.env['product.product'].sudo().create({
                'default_code': sku,
                'name': name,
                'list_price': float(sales_price) if sales_price else 0.0,
                'description': description,
                # Guardamos el descuento en el nuevo campo creado en el paso 1
                'x_brand_discount': float(discount) if discount else 0.0,
            })

            return {"status": "success", "message": "Product created successfully", "product_id": new_product.id}

        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}

    @http.route('/api/product', auth='user', methods=['PUT'], type='json', csrf=False)
    def update_product(self, **post):
        try:
            data = json.loads(request.httprequest.data)

            sku = data.get('sku')
            name = data.get('name')
            sales_price = data.get('sales_price')
            description = data.get('description')
            discount = data.get('discount') # Nuevo campo

            if not sku:
                return {"status": "error", "message": "Missing required field: sku"}

            product = request.env['product.product'].sudo().search([('default_code', '=', sku)], limit=1)
            if not product:
                return {"status": "error", "message": f"Product with SKU {sku} not found"}

            update_vals = {}
            if name:
                update_vals['name'] = name
            if sales_price:
                update_vals['list_price'] = float(sales_price)
            if description:
                update_vals['description'] = description
            
            # Actualizamos el descuento si viene en el JSON
            if discount is not None:
                update_vals['x_brand_discount'] = float(discount)

            product.write(update_vals)

            return {"status": "success", "message": "Product updated successfully", "product_id": product.id}

        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}

    @http.route('/api/product', auth='user', methods=['DELETE'], type='json', csrf=False)
    def delete_product(self, **post):
        try:
            data = json.loads(request.httprequest.data)
            sku = data.get('sku')

            if not sku:
                return {"status": "error", "message": "Missing required field: sku"}

            product = request.env['product.product'].sudo().search([('default_code', '=', sku)], limit=1)
            if not product:
                return {"status": "error", "message": f"Product with SKU {sku} not found"}

            product.unlink()
            return {"status": "success", "message": "Product deleted successfully"}

        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}