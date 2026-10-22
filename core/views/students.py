from django.utils.translation import gettext as _
from .common import *
from django.views.decorators.cache import never_cache

@login_required
def student_list(request):
    qs=students(request.user).order_by('name')
    if request.GET.get('q'): qs=qs.filter(name__icontains=request.GET['q'])
    return page(request,_('Alumnado'),students_list=qs,section='students')


@login_required
def student_edit(request,pk=None):
    require_admin(request.user)
    return generic_edit(request,DynamicStudentForm,_('Ficha del alumno'),get_object_or_404(Student,pk=pk) if pk else None,'students')


@login_required
@never_cache
def student_detail(request,pk):
    student=get_object_or_404(students(request.user),pk=pk)
    tab=request.GET.get('tab','summary')
    ctx={'student':student,'tab':tab,'section':'student','enrollments':student.enrollments.filter(group__in=groups(request.user)).select_related('group'),'can_sensitive':profile(request.user).sensitive_access}
    if tab=='restricted':
        require_sensitive(request.user,student); audit(request.user,'restricted:read',student)
        ctx['restricted']=student.restricted_notes.order_by('-created_at')
        ctx['support_plans']=student.support_plans.select_related('author').order_by('-created_at','-id')
        audit(request.user,'support:read',student)
    if tab=='learning': ctx['learning']=student.learning.filter(session__group__in=groups(request.user)).select_related('session','author').order_by('-created_at')
    if tab=='learning':
        from core.challenges import tier_for
        ctx['challenge_history']=[{'entry':entry,'count':len(entry.reached),'total':len(entry.specs),'tier':tier_for(len(entry.reached),len(entry.specs))} for entry in student.challenge_progress.filter(session__group__in=groups(request.user)).select_related('session','author').order_by('-created_at','-id')]
    if tab=='attendance': ctx['attendance']=Attendance.objects.filter(student=student,session__group__in=groups(request.user)).select_related('session').order_by('-session__start')
    if tab=='guardians': ctx['links']=student.guardians.select_related('guardian')
    if tab=='evidence': ctx['evidences']=student.evidences.filter(session__group__in=groups(request.user)).select_related('author')
    return page(request,student.name,**ctx)


@login_required
def enrollment(request,pk):
    require_admin(request.user)
    student=get_object_or_404(Student,pk=pk)
    error=''
    if request.method=='POST':
        try:
            destination=get_object_or_404(ClassGroup,pk=request.POST.get('group'))
            move_student(student,destination,date.fromisoformat(request.POST.get('starts','')),request.user,request.POST.get('previous') or None)
            return redirect('student',pk=pk)
        except (ValidationError,ValueError,Enrollment.DoesNotExist) as e: error=' '.join(e.messages) if isinstance(e,ValidationError) else _('Fecha o matrícula no válida.')
    return page(request,_('Matrícula y traslado'),section='enrollment',student=student,available_groups=ClassGroup.objects.filter(status='active'),enrollments=student.enrollments.filter(ends=None).select_related('group'),error=error)


@login_required
def guardian_edit(request,pk):
    require_admin(request.user)
    student=get_object_or_404(Student,pk=pk)
    form=LinkForm(request.POST or None)
    form.instance.student=student
    if request.method=='POST' and form.is_valid():
        form.save(); audit(request.user,'guardian:link',student); return redirect(reverse('student',args=[pk])+'?tab=guardians')
    return render(request,'core/form.html',{'title':_('Vincular responsable existente'),'form':form,'hint':_('Un responsable puede vincularse a varios hermanos. Si aún no existe, créalo en Configuración → Responsables.')})


@login_required
def restricted_edit(request,pk):
    student=get_object_or_404(students(request.user),pk=pk); require_sensitive(request.user,student)
    form=RestrictedForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False); obj.student=student; obj.author=request.user; obj.save()
        audit(request.user,'restricted:create',obj)
        return redirect(reverse('student',args=[pk])+'?tab=restricted')
    return render(request,'core/form.html',{'title':_('Información restringida'),'form':form,'hint':_('Registra únicamente información pertinente con finalidad definida. No introduzcas diagnósticos inferidos.')})


@login_required
def consent_add(request,pk):
    require_admin(request.user); student=get_object_or_404(Student,pk=pk)
    def prepare(form): form.instance.student=student
    return generic_edit(request,ConsentForm,_('Registrar autorización específica'),None,reverse('student',args=[pk]),prepare)


@login_required
def student_export(request,pk):
    require_admin(request.user)
    student=get_object_or_404(Student,pk=pk)
    if request.method=='POST':
        if request.POST.get('confirm')!='EXPORTAR': return HttpResponse(_('Confirma el alcance escribiendo EXPORTAR.'),status=400)
        include_sensitive=request.POST.get('sensitive')=='1'
        if include_sensitive: require_sensitive(request.user,student)
        from django.forms.models import model_to_dict
        def values(query): return list(query.values())
        data={'student':{f.name:getattr(student,f.name) for f in student._meta.fields},'enrollments':values(student.enrollments.all()),'responsible_links':[{**{f.name:getattr(link,f.attname) for f in link._meta.fields},'guardian':model_to_dict(link.guardian)} for link in student.guardians.select_related('guardian')],'consents':values(student.consents.all()),'learning':values(student.learning.all()),'challenge_progress':values(student.challenge_progress.all()),'attendance':values(Attendance.objects.filter(student=student)),'evidence_metadata':values(student.evidences.all())}
        if include_sensitive: data['restricted']=values(student.restricted_notes.all()); data['support_plans']=values(student.support_plans.all()); audit(request.user,'restricted:export',student)
        audit(request.user,'student:export',student)
        response=JsonResponse(data,json_dumps_params={'ensure_ascii':False,'indent':2});response['Content-Disposition']='attachment; filename="expediente.json"';response['Cache-Control']='no-store';return response
    return page(request,_('Exportación administrativa'),section='export',student=student,can_sensitive=profile(request.user).sensitive_access)


@login_required
def support_plan_edit(request,pk):
    student=get_object_or_404(students(request.user),pk=pk)
    require_sensitive(request.user,student)
    latest=student.support_plans.order_by('-created_at','-id').first()
    initial={key:getattr(latest,key) for key in ('active','adaptation_kind','neae_reported','nature','source','relevance','support','review')} if latest else {}
    initial['previous']=str(latest.pk) if latest else ''
    form=SupportPlanForm(request.POST or None,initial=initial)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                Student.objects.select_for_update().get(pk=student.pk)
                last=student.support_plans.order_by('-created_at','-id').first()
                if form.cleaned_data['previous']!=(str(last.pk) if last else ''):raise ValidationError(_('Otra persona ha modificado los apoyos. Recarga antes de guardar.'))
                obj=form.save(commit=False);obj.student=student;obj.author=request.user;obj.supersedes=last;obj.save()
                audit(request.user,'support:revision',obj)
            return redirect(reverse('student',args=[pk])+'?tab=restricted')
        except ValidationError as exc:fail(form,exc)
    audit(request.user,'support:read',student)
    response=render(request,'core/form.html',{'title':_('Adaptación educativa y NEAE comunicada'),'form':form,'hint':_('Registra apoyos necesarios, fuente y revisión. Esta marca no genera un diagnóstico. Desmarca la adaptación para finalizarla conservando el historial. Solo es visible con permiso de información restringida.')})
    response['Cache-Control']='no-store'
    return response
