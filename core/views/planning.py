from django.utils.translation import gettext as _
from .common import *
from django.views.decorators.cache import never_cache
from django.db import models
from core.challenges import specs_for, diversity_for, progress_for, save_progress, sections, scale_for

@login_required
def calendar_view(request):
    try: selected=date.fromisoformat(request.GET.get('date',str(timezone.localdate())))
    except ValueError: selected=timezone.localdate()
    mode=request.GET.get('view','week')
    if mode=='month': start=selected.replace(day=1); end=(start+timedelta(days=32)).replace(day=1)
    elif mode=='day': start=selected; end=start+timedelta(days=1)
    else: mode='week'; start=selected-timedelta(days=selected.weekday()); end=start+timedelta(days=7)
    qs=session_q(request.user).filter(start__date__gte=start,start__date__lt=end).order_by('start')
    for key,lookup in [('group','group_id'),('teacher','teacher_id'),('location','group__location'),('kind','group__kind')]:
        if request.GET.get(key):
            try: qs=qs.filter(**{lookup:request.GET[key]})
            except (ValueError,ValidationError): qs=qs.none()
    days=[]; cursor=start
    while cursor<end:
        days.append({'date':cursor,'sessions':[s for s in qs if timezone.localtime(s.start).date()==cursor],'holiday':Holiday.objects.filter(start__lte=cursor,end__gte=cursor).first()}); cursor+=timedelta(days=1)
    return render(request,'core/calendar.html',{'title':_('Calendario'),'days':days,'mode':mode,'selected':selected,'previous':start-timedelta(days=1),'following':end,'groups':groups(request.user),'teachers':User.objects.filter(classgroup__in=groups(request.user)).distinct(),'locations':groups(request.user).values_list('location',flat=True).distinct(),'types':ClassGroup.TYPES})


@login_required
def session_edit(request,pk=None):
    instance=get_object_or_404(session_q(request.user),pk=pk) if pk else None
    if not educational(request.user): raise PermissionDenied
    form=SessionForm(request.POST or None,instance=instance)
    form.fields['group'].queryset=groups(request.user).filter(status='active')
    form.fields['teacher'].queryset=User.objects.filter(classgroup__in=groups(request.user),is_active=True).distinct()
    initial_template=current()['session_template']
    if not instance: form.fields['planned'].initial=initial_template
    if request.method=='POST' and form.is_valid():
        try:
            count=int(request.POST.get('repeat','1'))
            if not 1<=count<=52: raise ValidationError(_('Repeticiones: de 1 a 52.'))
            if instance and count!=1: raise ValidationError(_('Para repetir, crea una serie nueva.'))
            with transaction.atomic():
                obj=form.save(commit=False)
                session_errors(obj,obj.pk if instance else None)
                # Freeze library content when selecting a new resource; edits do not mutate prior snapshots.
                if not instance or 'resource' in form.changed_data: obj.resource_snapshot=snapshot(obj.resource)
                if not obj.content_area and obj.resource: obj.content_area=obj.resource.content_area
                sid=uuid.uuid4() if count>1 else None
                if not instance: obj.series=sid
                obj=save_versioned(form,request.user)
                # form.save() reuses its instance, including snapshot and series assignments.
                if not instance and count>1:
                    from copy import copy
                    for n in range(1,count):
                        copy_obj=copy(obj); copy_obj.pk=uuid.uuid4(); copy_obj._state.adding=True
                        copy_obj.start=obj.start+timedelta(weeks=n); copy_obj.end=obj.end+timedelta(weeks=n); copy_obj.number=obj.number+n
                        session_errors(copy_obj); copy_obj.save()
                if instance and request.POST.get('scope')=='following' and obj.series:
                    delta_start=obj.start-form.initial['start']; delta_end=obj.end-form.initial['end']
                    later=Session.objects.filter(series=obj.series,start__gt=form.initial['start']).exclude(pk=obj.pk)
                    for later_obj in later:
                        if not groups(request.user).filter(pk=later_obj.group_id).exists(): raise PermissionDenied
                        if later_obj.status=='done': raise ValidationError(_('La serie contiene registros realizados. Modifica solo esta sesión para conservarlos.'))
                        later_obj.start+=delta_start; later_obj.end+=delta_end
                        later_obj.teacher=obj.teacher; later_obj.status=obj.status
                        session_errors(later_obj,later_obj.pk); later_obj.version+=1; later_obj.save()
            messages.success(request,_('Sesión guardada. La fecha no completa aprendizajes automáticamente.')); return redirect('session',pk=obj.pk)
        except (ValidationError,ValueError) as e: fail(form,e if isinstance(e,ValidationError) else _('Repeticiones no válidas.'))
    return render(request,'core/form.html',{'title':_('Editar sesión') if instance else _('Planificar una clase'),'form':form,'session_form':True,'editing':bool(instance),'series':instance.series if instance else None})


@login_required
@never_cache
def session_detail(request,pk):
    obj=get_object_or_404(session_q(request.user),pk=pk)
    day=timezone.localtime(obj.start).date()
    roster=Student.objects.filter(enrollments__group=obj.group,enrollments__starts__lte=day).filter(Q(enrollments__ends=None)|Q(enrollments__ends__gte=day)).distinct().order_by('name')
    specs=specs_for(obj)
    rows=[{'student':s,'attendance':Attendance.objects.filter(session=obj,student=s).first(),'learning':Learning.objects.filter(session=obj,student=s).order_by('-created_at').first()} for s in roster]
    for row in rows:
        row['challenge_progress']=progress_for(obj,row['student'],specs)
        if profile(request.user).sensitive_access:
            row['support_plan']=row['student'].support_plans.order_by('-created_at','-id').first()
            if row['support_plan']:audit(request.user,'support:read',row['student'])
    outline=sections(obj.planned)
    outline={k:v for k,v in outline.items() if k not in ('Retos desbloqueables','Atención a la diversidad','Preparar antes de la clase','Ladrillos que trabajamos')}
    draft_values={k:request.POST.getlist(k) if k.startswith('reached_') else v for k,v in request.POST.items()} if request.method=='POST' else {}
    if request.method=='POST':
        for row in rows:
            key=str(row['student'].pk)
            if request.POST.get('track_'+key)=='1':draft_values['reached_'+key]=request.POST.getlist('reached_'+key)
    return render(request,'core/session.html',{'challenge_scale':scale_for(len(specs)) if specs else [],'challenge_specs':specs,'diversity':diversity_for(obj),'outline':outline,'title':obj.title,'session':obj,'rows':rows,'attendance_states':Attendance.STATES,'learning_states':learning_states(),'rubrics':current()['rubrics'] if current()['flags'].get('rubrics',True) else [],'custom_fields':current()['custom_fields'],'draft_values':draft_values})


@login_required
@require_POST
def class_save(request,pk):
    obj=get_object_or_404(session_q(request.user),pk=pk)
    try:
        with transaction.atomic():
            expected=int(request.POST.get('version','0'))
            if obj.version!=expected: raise ValidationError(_('La sesión ha cambiado. Recarga antes de guardar.'))
            if obj.status in ('cancelled','recover'): raise ValidationError(_('No puedes registrar una sesión cancelada o pendiente de recuperar.'))
            day=timezone.localtime(obj.start).date()
            roster=Student.objects.filter(enrollments__group=obj.group,enrollments__starts__lte=day).filter(Q(enrollments__ends=None)|Q(enrollments__ends__gte=day)).distinct()
            for student in roster:
                save_progress(obj,student,request.user,request.POST)
                key=str(student.pk)
                status=request.POST.get('attendance_'+key,'')
                if status:
                    if status not in dict(Attendance.STATES): raise ValidationError(_('Estado de asistencia no válido.'))
                    Attendance.objects.update_or_create(session=obj,student=student,defaults={'status':status,'note':request.POST.get('note_'+key,'')[:250]})
                if request.POST.get('record_'+key):
                    state=request.POST.get('state_'+key,learning_states()[0][0]); learning_state=request.POST.get('learning_'+key,learning_states()[0][0])
                    if state not in dict(learning_states()) or learning_state not in dict(learning_states()): raise ValidationError(_('Estado de aprendizaje no válido.'))
                    challenge=request.POST.get('challenge_'+key,'').strip() or request.POST.get('common_activity','').strip()
                    if not challenge: raise ValidationError(_('Indica el reto trabajado para cada registro seleccionado.'))
                    rubric={r:request.POST.get('rubric_'+key+'_'+str(n),'')[:200] for n,r in enumerate(current()['rubrics'] if current()['flags'].get('rubrics',True) else [])}
                    previous=Learning.objects.filter(session=obj,student=student).order_by('-created_at').first()
                    Learning.objects.create(session=obj,student=student,author=request.user,challenge=challenge[:200],evidence=request.POST.get('evidence_'+key,''),achievement=request.POST.get('achievement_'+key,''),difficulty=request.POST.get('difficulty_'+key,''),objective=request.POST.get('objective_'+key,''),support=request.POST.get('support_'+key,''),student_comment=request.POST.get('comment_'+key,''),next_step=request.POST.get('next_'+key,''),internal_notes=request.POST.get('private_'+key,''),activity_status=state,learning_status=learning_state,rubric=rubric,supersedes=previous)
            values={k:request.POST.get(k,'') for k in ('actual','pending','adaptations','notes','next_steps')}
            values['status']='done' if request.POST.get('close') else obj.status
            if values['status']=='done' and not values['actual'].strip(): raise ValidationError(_('Describe lo realizado antes de cerrar la sesión.'))
            if not Session.objects.filter(pk=obj.pk,version=expected).update(**values,version=expected+1,updated_at=timezone.now()): raise ValidationError(_('Conflicto de edición. Recarga y vuelve a intentarlo.'))
            audit(request.user,'session:close' if request.POST.get('close') else 'session:draft',obj)
        messages.success(request,_('Clase guardada. Los registros individuales conservan sus versiones anteriores.'))
    except (ValidationError,ValueError) as e:
        messages.error(request,' '.join(e.messages) if isinstance(e,ValidationError) else _('Versión no válida.'))
        response=session_detail(request,pk); response.status_code=422; return response
    return redirect('session',pk=pk)


@login_required
def recover_session(request,pk):
    source=get_object_or_404(session_q(request.user),pk=pk)
    if source.status not in ('recover','cancelled'): return HttpResponse(_('Solo se recuperan sesiones canceladas o pendientes.'),status=400)
    form=SessionForm(request.POST or None,initial={k:getattr(source,k) for k in ['group','teacher','content_area','title','number','resource','goals','materials','planned','diversity']})
    form.fields['group'].queryset=groups(request.user)
    form.fields['teacher'].queryset=User.objects.filter(classgroup__in=groups(request.user)).distinct()
    if request.method=='POST' and form.is_valid():
        try:
            obj=form.save(commit=False); obj.recovery_of=source; obj.resource_snapshot=source.resource_snapshot
            obj.challenge_specs=specs_for(source); obj.diversity=diversity_for(source)
            session_errors(obj); obj.save(); audit(request.user,'session:recover',obj); return redirect('session',pk=obj.pk)
        except ValidationError as e: fail(form,e)
    return render(request,'core/form.html',{'title':_('Recuperar sesión · se conserva la original'),'form':form})


@login_required
def challenge_edit(request,pk):
    from django.forms import formset_factory
    from core.challenges import specs_for,validate_specs
    obj=get_object_or_404(session_q(request.user),pk=pk)
    if not educational(request.user):raise PermissionDenied
    Factory=formset_factory(ChallengeSpecForm,extra=2,max_num=30,validate_max=True,absolute_max=35)
    specs=specs_for(obj)
    formset=Factory(request.POST or None,initial=specs)
    error=''
    if request.method=='POST' and formset.is_valid():
        try:
            updated=[]
            for values in formset.cleaned_data:
                if not values or not values.get('title'):
                    if values.get('hint') or values.get('criteria'):raise ValidationError(_('Indica la consigna de cada reto.'))
                    continue
                updated.append({'id':f'R{len(updated)+1}',**{k:values[k] for k in ('title','hint','criteria')}})
            validate_specs(updated)
            with transaction.atomic():
                fresh=Session.objects.select_for_update().get(pk=obj.pk)
                if ChallengeProgress.objects.filter(session=fresh).exists():raise ValidationError(_('Los retos ya tienen seguimiento. Conserva esta versión y prepara otra sesión para cambiarlos.'))
                if not Session.objects.filter(pk=obj.pk,version=request.POST.get('version','0')).update(challenge_specs=updated,resource_snapshot={**fresh.resource_snapshot,'challenges_configured':True},version=models.F('version')+1,updated_at=timezone.now()):raise ValidationError(_('La sesión ha cambiado. Recarga antes de guardar.'))
                audit(request.user,'challenge:configure',obj)
            return redirect('session',pk=pk)
        except (ValidationError,ValueError) as exc:error=' '.join(exc.messages) if isinstance(exc,ValidationError) else _('Versión no válida.')
    return render(request,'core/challenge_edit.html',{'title':_('Organizar retos'),'session':obj,'formset':formset,'error':error,'locked':ChallengeProgress.objects.filter(session=obj).exists()})


def deletion_blocked(obj):
    return (obj.status!='planned' or any(getattr(obj,k).strip() for k in ('actual','pending','adaptations','notes','next_steps')) or
            Attendance.objects.filter(session=obj).exists() or Learning.objects.filter(session=obj).exists() or
            Evidence.objects.filter(session=obj).exists() or ChallengeProgress.objects.filter(session=obj).exists() or
            Session.objects.filter(recovery_of=obj).exists() or bool(obj.recovery_of_id))


@login_required
def session_delete(request,pk):
    require_admin(request.user)
    obj=get_object_or_404(session_q(request.user),pk=pk)
    blocked=deletion_blocked(obj);error=''
    if request.method=='POST':
        try:
            with transaction.atomic():
                fresh=Session.objects.select_for_update().get(pk=pk)
                if deletion_blocked(fresh):raise ValidationError(_('Esta sesión tiene historial o ya no es un borrador vacío. Puedes cancelarla conservando sus registros.'))
                if request.POST.get('confirm')!='ELIMINAR' or request.POST.get('version')!=str(fresh.version):raise ValidationError(_('Escribe ELIMINAR y comprueba que la sesión no ha cambiado.'))
                audit(request.user,'session:delete',fresh)
                fresh.delete()
            messages.success(request,_('Sesión eliminada. El grupo, el alumnado y las demás sesiones se conservan.'))
            return redirect('calendar')
        except ValidationError as exc:error=' '.join(exc.messages)
    return render(request,'core/session_delete.html',{'title':_('Eliminar sesión de prueba'),'session':obj,'blocked':blocked,'error':error})
