from django.utils.translation import gettext as _
from .common import *

@login_required
def group_list(request):
    from core.list_filters import GroupListFilters, text_search
    allowed = groups(request.user)
    data = request.POST if request.method == 'POST' else request.GET
    form = GroupListFilters(data, allowed_groups=allowed)
    qs = allowed.select_related('year')
    if form.is_valid():
        values = form.cleaned_data
        for field in ('kind', 'year', 'location', 'status'):
            if values[field]:
                qs = qs.filter(**{field: values[field]})
        qs = text_search(qs, values['q'], 'name', 'location', 'schedule')
        qs = qs.order_by(values['order'] or 'name', 'name', 'pk')
    else:
        qs = qs.none()
    response = page(request, _('Grupos'), groups_list=qs, section='groups', list_filters=form,
                    result_count=qs.count(), has_list_filters=any(data.get(k) for k in form.fields if k != 'order'))
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
def group_detail(request,pk):
    group=get_object_or_404(groups(request.user),pk=pk)
    return page(request,group.name,group=group,enrollments=group.enrollments.select_related('student').filter(ends=None),sessions=session_q(request.user).filter(group=group).order_by('-start'),section='group')


@login_required
def group_edit(request,pk=None):
    require_admin(request.user)
    return generic_edit(request,GroupForm,_('Editar grupo') if pk else _('Nuevo grupo'),get_object_or_404(ClassGroup,pk=pk) if pk else None,'groups')
