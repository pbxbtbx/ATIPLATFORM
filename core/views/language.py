from django.utils.translation import gettext as _
"""Cambio de idioma sin traducir ni enviar contenido del alumnado a terceros."""
from django import forms
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from core.access import profile, audit

@require_POST
def set_language(request):
    language=request.POST.get('language')
    if language not in dict(settings.LANGUAGES): return HttpResponse(_('Idioma no válido.'),status=400)
    if request.user.is_authenticated:
        account=profile(request.user);account.language=language;account.save(update_fields=['language'])
        audit(request.user,'language:update',account)
    next_url=request.POST.get('next','/')
    if not url_has_allowed_host_and_scheme(next_url,{request.get_host()},require_https=request.is_secure()): next_url='/'
    response=redirect(next_url)
    response.set_cookie('atigra_language',language,max_age=31536000,httponly=True,samesite='Lax',secure=settings.SESSION_COOKIE_SECURE)
    return response
