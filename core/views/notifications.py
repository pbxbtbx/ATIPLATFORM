from django.utils.translation import gettext as _
"""Recordatorios privados del docente; nunca agrega datos de otros usuarios."""
from .common import *

@login_required
def notifications(request):
    status=request.GET.get('status','pending')
    if status not in ('pending','done','all'): status='pending'
    tasks=Task.objects.filter(author=request.user).order_by('done','due','created_at')
    if status=='pending': tasks=tasks.filter(done=False)
    elif status=='done': tasks=tasks.filter(done=True)
    return render(request,'core/notifications.html',{'title':_('Notificaciones'),'tasks':tasks,'status_filter':status,'today':timezone.localdate()})

@login_required
@require_POST
def task_toggle(request,pk):
    task=get_object_or_404(Task,pk=pk,author=request.user)
    action=request.POST.get('action')
    if action not in ('complete','reopen'): return HttpResponse(_('Acción no válida.'),status=400)
    task.done=action=='complete';task.save(update_fields=['done','updated_at'])
    audit(request.user,'reminder:complete' if task.done else 'reminder:reopen',task)
    messages.success(request,_('Recordatorio completado.') if task.done else _('Recordatorio reabierto.'))
    return redirect('notifications')
