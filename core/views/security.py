from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import timedelta
from core.access import require_developer, audit
from core.models import BackupCheck, TechnicalEvent, Audit
from core.security_review import integrity, runtime_checks, scan_evidence


@login_required
@require_GET
@never_cache
def security_view(request):
    require_developer(request.user)
    audit(request.user, 'security:view')
    check = integrity()
    backup = BackupCheck.objects.filter(verified_at__isnull=False).order_by('-verified_at').first()
    response = render(request, 'core/security.html', {
        'title': _('Integridad y seguridad'), 'integrity': check, 'checks': runtime_checks(), 'evidence': scan_evidence(check),
        'backup_recent': bool(backup and backup.verified_at >= timezone.now() - timedelta(days=7)),
        'backup_verified': backup.verified_at if backup else None,
        'events': TechnicalEvent.objects.order_by('-created_at')[:20],
        'security_audits': Audit.objects.filter(action='security:view').order_by('-created_at')[:20],
    })
    response['Cache-Control'] = 'private, no-store'
    response['X-Robots-Tag'] = 'noindex, nofollow'
    return response
