class MercadoPagoCSPMiddleware:
    """
    Middleware para agregar encabezados de Content Security Policy
    que permitan la carga de recursos de Mercado Pago
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar encabezados CSP solo para páginas que usan Mercado Pago
        if '/checkout_counters/' in request.path or '/payment/' in request.path:
            # Dominios de Mercado Pago que necesitan ser permitidos
            mp_domains = [
                'https://http2.mlstatic.com',
                'https://sdk.mercadopago.com',
                'https://secure.mlstatic.com',
                'https://www.mercadopago.com',
                'https://api.mercadopago.com',
            ]
            
            # Construir la política CSP
            csp_parts = {
                'default-src': ["'self'"],
                'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"] + mp_domains,
                'style-src': ["'self'", "'unsafe-inline'"] + mp_domains,
                'img-src': ["'self'", "data:"] + mp_domains,
                'font-src': ["'self'"] + mp_domains,
                'connect-src': ["'self'"] + mp_domains,
                'frame-src': ["'self'"] + mp_domains,
            }
            
            # Convertir a string
            csp_string = '; '.join([
                f"{key} {' '.join(value)}"
                for key, value in csp_parts.items()
            ])
            
            # Agregar el encabezado
            response['Content-Security-Policy'] = csp_string
        
        return response
