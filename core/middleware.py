from django.utils.translation import gettext as _
from django.http import HttpResponse
class MaintenanceMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        from .configuration import current
        from .access import developer
        if request.user.is_authenticated and not request.path.startswith(('/developer/','/privacy/erasure/','/logout/','/static/')):
            if current()['maintenance'] and not developer(request.user):
                return HttpResponse(_('Atigra Makers está en mantenimiento. Inténtalo más tarde.'),status=503)
        return self.get_response(request)


from django.utils.deprecation import MiddlewareMixin
class SafeErrorMiddleware(MiddlewareMixin):
    def process_exception(self,request,exception):
        from django.core.exceptions import PermissionDenied,ValidationError
        from django.http import Http404
        if isinstance(exception,(PermissionDenied,ValidationError,Http404)): return None
        from .models import TechnicalEvent
        try:
            # Never persist str(exception), URL, user, query string or traceback.
            TechnicalEvent.objects.create(code='APPLICATION_ERROR')
        # Security review: failed redacted telemetry must not mask the original exception.
        except Exception:  # nosec B110
            pass
        return None


class UserLanguageMiddleware:
    """Idioma por cuenta, o cookie de idioma para la pantalla de acceso."""
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        from django.utils import translation
        from django.utils.cache import patch_vary_headers
        from .access import profile
        language=profile(request.user).language if request.user.is_authenticated else request.COOKIES.get('atigra_language','es')
        if language not in ('es','en'): language='es'
        request.LANGUAGE_CODE=language
        with translation.override(language):
            response=self.get_response(request)
            response.headers.setdefault('Content-Language',language)
        patch_vary_headers(response,('Cookie',))
        return response


class ErasureOnlyMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        from django.conf import settings
        from django.shortcuts import redirect
        from .access import admin, profile
        if not settings.ERASURE_ONLY or request.path.startswith(('/login/', '/logout/', '/static/')):
            return self.get_response(request)
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if not admin(request.user) or not profile(request.user).sensitive_access:
            return HttpResponse(_('Acceso temporalmente restringido para retirar datos del piloto.'), status=403)
        if not request.path.startswith('/privacy/erasure/'):
            return redirect('erasure_select')
        return self.get_response(request)
