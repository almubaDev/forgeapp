from django.contrib.sessions.exceptions import SessionInterrupted
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
import logging
import json

logger = logging.getLogger('forgeapp')

class SessionHandlingMiddleware(MiddlewareMixin):
    """
    Custom middleware to handle session interruption issues.
    This middleware catches SessionInterrupted exceptions that occur during 
    payment processing and provides a graceful fallback mechanism.
    """
    
    def process_exception(self, request, exception):
        if isinstance(exception, SessionInterrupted):
            logger.warning(
                "SessionInterrupted exception caught. User session was deleted before request completed. "
                f"Path: {request.path}, User: {request.user if request.user.is_authenticated else 'Anonymous'}"
            )
            
            # Check if this is a payment-related request
            if '/finance/' in request.path or 'payment' in request.path or 'subscription' in request.path:
                logger.info(f"Payment-related request intercepted at: {request.path}")
                
                # Check if this is an AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # Return a JSON response for AJAX requests
                    response_data = {
                        'status': 'success',
                        'message': 'Pago procesado correctamente. Por favor refresque la página para ver los cambios.',
                        'redirect': '/dashboard/'
                    }
                    return HttpResponse(
                        json.dumps(response_data),
                        content_type="application/json",
                        status=200
                    )
                
                # For regular requests, redirect to dashboard with a success message
                response = redirect('/dashboard/')
                messages.success(
                    request, 
                    'La operación se ha completado correctamente. El sistema está procesando su pago.'
                )
                return response
            
            # For other types of requests, let Django handle the exception
            logger.info(f"Non-payment request with SessionInterrupted: {request.path}")
            return None
