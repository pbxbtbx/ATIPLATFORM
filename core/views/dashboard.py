from django.utils.translation import gettext as _
from .common import *

@login_required
def home(request):
    today=timezone.localdate()
    sessions=session_q(request.user)
    upcoming=sessions.filter(start__date__gte=today).exclude(status__in=['cancelled','recover']).order_by('start')[:5]
    return render(request,'core/home.html',{'title':_('Un nuevo día para crear'),'today':today,'sessions':sessions.filter(start__date=today).order_by('start'),'upcoming':upcoming,'pending':sessions.filter(start__date__lt=today,status='planned').order_by('-start')[:5],'group_count':groups(request.user).filter(status='active').count(),'student_count':students(request.user).filter(status='active').count(),'tasks':Task.objects.filter(author=request.user,done=False).order_by('due')[:8]})


@login_required
def task_add(request):
    def prepare(form): form.instance.author=request.user
    return generic_edit(request,TaskForm,_('Recordatorio docente'),None,'notifications',prepare)


@login_required
@require_POST
def task_done(request,pk):
    obj=get_object_or_404(Task,pk=pk,author=request.user); obj.done=True; obj.save(); return redirect('home')

