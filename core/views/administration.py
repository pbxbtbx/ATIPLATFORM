from django.utils.translation import gettext as _
from .common import *

@login_required
def settings_view(request):
    require_admin(request.user)
    return page(request,_('Configuración'),section='settings',years=AcademicYear.objects.order_by('-starts'),users=User.objects.select_related('profile').order_by('username'),guardians=Guardian.objects.all(),holidays=Holiday.objects.order_by('start'))


@login_required
def admin_form(request,kind,pk=None):
    require_admin(request.user)
    mapping={'year':(YearForm,AcademicYear,_('Curso académico')),'guardian':(GuardianForm,Guardian,_('Responsable')),'holiday':(HolidayForm,Holiday,_('Periodo sin clase'))}
    if kind not in mapping: return HttpResponse(status=404)
    form,model,title=mapping[kind]
    return generic_edit(request,form,title,get_object_or_404(model,pk=pk) if pk else None,'settings')


@login_required
def user_add(request):
    require_admin(request.user); form=UserForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            data=form.cleaned_data; user=User.objects.create_user(username=data['username'],first_name=data['first_name'],password=data['password'])
            Profile.objects.create(user=user,role=data['role'],sensitive_access=data['sensitive_access'],development_access=data['development_access']); audit(request.user,'user:create',user)
        return redirect('settings')
    return render(request,'core/form.html',{'title':_('Crear usuario interno'),'form':form})


@login_required
def user_edit(request,pk):
    require_admin(request.user)
    target=get_object_or_404(User,pk=pk)
    target_profile=profile(target)
    form=EditUserForm(request.POST or None,initial={'first_name':target.first_name,'role':target_profile.role,'active':target.is_active,'sensitive_access':target_profile.sensitive_access,'development_access':target_profile.development_access})
    if request.method=='POST' and form.is_valid():
        if target==request.user and (not form.cleaned_data['active'] or form.cleaned_data['role']!='admin'):
            form.add_error(None,_('No puedes quitarte tu propio acceso de administración.'))
        else:
            with transaction.atomic():
                target.first_name=form.cleaned_data['first_name']; target.is_active=form.cleaned_data['active']; target.save()
                target_profile.role=form.cleaned_data['role']; target_profile.sensitive_access=form.cleaned_data['sensitive_access']; target_profile.development_access=form.cleaned_data['development_access']; target_profile.save()
                audit(request.user,'user:permissions',target)
            return redirect('settings')
    return render(request,'core/form.html',{'title':_('Permisos de ')+target.username,'form':form})
