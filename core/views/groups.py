from django.utils.translation import gettext as _
from .common import *

@login_required
def group_list(request):
    return page(request,_('Grupos'),groups_list=groups(request.user).select_related('year').order_by('name'),section='groups')


@login_required
def group_detail(request,pk):
    group=get_object_or_404(groups(request.user),pk=pk)
    return page(request,group.name,group=group,enrollments=group.enrollments.select_related('student').filter(ends=None),sessions=session_q(request.user).filter(group=group).order_by('-start'),section='group')


@login_required
def group_edit(request,pk=None):
    require_admin(request.user)
    return generic_edit(request,GroupForm,_('Editar grupo') if pk else _('Nuevo grupo'),get_object_or_404(ClassGroup,pk=pk) if pk else None,'groups')
