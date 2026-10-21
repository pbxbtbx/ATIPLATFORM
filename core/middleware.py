from django.http import HttpResponse
class MaintenanceMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        from .configuration import current
        from .access import developer
        if request.user.is_authenticated and not request.path.startswith(('/developer/','/logout/','/static/')):
            if current()['maintenance'] and not developer(request.user):
                return HttpResponse('Atigra Makers está en mantenimiento. Inténtalo más tarde.',status=503)
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
        except Exception:
            pass
        return None
