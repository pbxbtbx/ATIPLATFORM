import calendar, csv, io, json, uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, connection
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from .access import *
from .services import *
from .configuration import current, validate_config, learning_states

def fail(form,exc): form.add_error(None,exc)
def page(request,title,**ctx): return render(request,'core/page.html',{'title':title,**ctx})
def session_q(user): return Session.objects.filter(group__in=groups(user)).select_related('group','teacher')
def require_module(user,name):
    if not educational(user) or not current()['modules'].get(name,True): raise PermissionDenied

def generic_edit(request,form_class,title,instance=None,back='home',prepare=None):
    form=form_class(request.POST or None,request.FILES or None,instance=instance)
    if prepare: prepare(form)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic(): obj=save_versioned(form,request.user)
            messages.success(request,'Cambios guardados.'); return redirect(back)
        except ValidationError as e: fail(form,e)
    return render(request,'core/form.html',{'title':title,'form':form})

@login_required
def home(request):
    today=timezone.localdate()
    sessions=session_q(request.user)
    upcoming=sessions.filter(start__date__gte=today).exclude(status__in=['cancelled','recover']).order_by('start')[:5]
    return render(request,'core/home.html',{'title':'Un nuevo día para crear','today':today,'sessions':sessions.filter(start__date=today).order_by('start'),'upcoming':upcoming,'pending':sessions.filter(start__date__lt=today,status='planned').order_by('-start')[:5],'group_count':groups(request.user).filter(status='active').count(),'student_count':students(request.user).filter(status='active').count(),'tasks':Task.objects.filter(author=request.user,done=False).order_by('due')[:8]})

@login_required
def group_list(request):
    return page(request,'Grupos',groups_list=groups(request.user).select_related('year').order_by('name'),section='groups')

@login_required
def group_detail(request,pk):
    group=get_object_or_404(groups(request.user),pk=pk)
    return page(request,group.name,group=group,enrollments=group.enrollments.select_related('student').filter(ends=None),sessions=session_q(request.user).filter(group=group).order_by('-start'),section='group')

@login_required
def group_edit(request,pk=None):
    require_admin(request.user)
    return generic_edit(request,GroupForm,'Editar grupo' if pk else 'Nuevo grupo',get_object_or_404(ClassGroup,pk=pk) if pk else None,'groups')

@login_required
def student_list(request):
    qs=students(request.user).order_by('name')
    if request.GET.get('q'): qs=qs.filter(name__icontains=request.GET['q'])
    return page(request,'Alumnado',students_list=qs,section='students')

@login_required
def student_edit(request,pk=None):
    require_admin(request.user)
    return generic_edit(request,DynamicStudentForm,'Ficha del alumno',get_object_or_404(Student,pk=pk) if pk else None,'students')

@login_required
def student_detail(request,pk):
    student=get_object_or_404(students(request.user),pk=pk)
    tab=request.GET.get('tab','summary')
    ctx={'student':student,'tab':tab,'section':'student','enrollments':student.enrollments.filter(group__in=groups(request.user)).select_related('group'),'can_sensitive':profile(request.user).sensitive_access}
    if tab=='restricted':
        require_sensitive(request.user,student); audit(request.user,'restricted:read',student)
        ctx['restricted']=student.restricted_notes.order_by('-created_at')
    if tab=='learning': ctx['learning']=student.learning.filter(session__group__in=groups(request.user)).select_related('session','author').order_by('-created_at')
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
        except (ValidationError,ValueError,Enrollment.DoesNotExist) as e: error=' '.join(e.messages) if isinstance(e,ValidationError) else 'Fecha o matrícula no válida.'
    return page(request,'Matrícula y traslado',section='enrollment',student=student,available_groups=ClassGroup.objects.filter(status='active'),enrollments=student.enrollments.filter(ends=None).select_related('group'),error=error)

@login_required
def guardian_edit(request,pk):
    require_admin(request.user)
    student=get_object_or_404(Student,pk=pk)
    form=LinkForm(request.POST or None)
    form.instance.student=student
    if request.method=='POST' and form.is_valid():
        form.save(); audit(request.user,'guardian:link',student); return redirect(reverse('student',args=[pk])+'?tab=guardians')
    return render(request,'core/form.html',{'title':'Vincular responsable existente','form':form,'hint':'Un responsable puede vincularse a varios hermanos. Si aún no existe, créalo en Configuración → Responsables.'})

@login_required
def restricted_edit(request,pk):
    student=get_object_or_404(students(request.user),pk=pk); require_sensitive(request.user,student)
    form=RestrictedForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False); obj.student=student; obj.author=request.user; obj.save()
        audit(request.user,'restricted:create',obj)
        return redirect(reverse('student',args=[pk])+'?tab=restricted')
    return render(request,'core/form.html',{'title':'Información restringida','form':form,'hint':'Registra únicamente información pertinente con finalidad definida. No introduzcas diagnósticos inferidos.'})

@login_required
def library(request):
    require_module(request.user,'library')
    qs=Resource.objects.order_by('domain','title')
    if request.GET.get('q'): qs=qs.filter(Q(title__icontains=request.GET['q'])|Q(domain__icontains=request.GET['q']))
    return page(request,'Biblioteca maker',resources=qs,section='library',sequences=Sequence.objects.filter(group__in=groups(request.user)))

@login_required
def resource_edit(request,pk=None):
    require_module(request.user,'library')
    return generic_edit(request,ResourceForm,'Recurso de aprendizaje',get_object_or_404(Resource,pk=pk) if pk else None,'library')

@login_required
def sequence_edit(request):
    require_module(request.user,'library')
    form=SequenceForm(request.POST or None); form.fields['group'].queryset=groups(request.user)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False); obj.snapshot=[snapshot(r) for r in form.cleaned_data['resources']]; obj.save(); form.save_m2m(); audit(request.user,'sequence:create',obj)
        return redirect('library')
    return render(request,'core/form.html',{'title':'Asignar secuencia (copia histórica)','form':form})

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
    return render(request,'core/calendar.html',{'title':'Calendario','days':days,'mode':mode,'selected':selected,'previous':start-timedelta(days=1),'following':end,'groups':groups(request.user),'teachers':User.objects.filter(classgroup__in=groups(request.user)).distinct(),'locations':groups(request.user).values_list('location',flat=True).distinct(),'types':ClassGroup.TYPES})

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
            if not 1<=count<=52: raise ValidationError('Repeticiones: de 1 a 52.')
            if instance and count!=1: raise ValidationError('Para repetir, crea una serie nueva.')
            with transaction.atomic():
                obj=form.save(commit=False)
                session_errors(obj,obj.pk if instance else None)
                # Freeze library content when selecting a new resource; edits do not mutate prior snapshots.
                if not instance or 'resource' in form.changed_data: obj.resource_snapshot=snapshot(obj.resource)
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
                        if later_obj.status=='done': raise ValidationError('La serie contiene registros realizados. Modifica solo esta sesión para conservarlos.')
                        later_obj.start+=delta_start; later_obj.end+=delta_end
                        later_obj.teacher=obj.teacher; later_obj.status=obj.status
                        session_errors(later_obj,later_obj.pk); later_obj.version+=1; later_obj.save()
            messages.success(request,'Sesión guardada. La fecha no completa aprendizajes automáticamente.'); return redirect('session',pk=obj.pk)
        except (ValidationError,ValueError) as e: fail(form,e if isinstance(e,ValidationError) else 'Repeticiones no válidas.')
    return render(request,'core/form.html',{'title':'Editar sesión' if instance else 'Planificar una clase','form':form,'session_form':True,'editing':bool(instance),'series':instance.series if instance else None})

@login_required
def session_detail(request,pk):
    obj=get_object_or_404(session_q(request.user),pk=pk)
    day=timezone.localtime(obj.start).date()
    roster=Student.objects.filter(enrollments__group=obj.group,enrollments__starts__lte=day).filter(Q(enrollments__ends=None)|Q(enrollments__ends__gte=day)).distinct().order_by('name')
    rows=[{'student':s,'attendance':Attendance.objects.filter(session=obj,student=s).first(),'learning':Learning.objects.filter(session=obj,student=s).order_by('-created_at').first()} for s in roster]
    return render(request,'core/session.html',{'title':obj.title,'session':obj,'rows':rows,'attendance_states':Attendance.STATES,'learning_states':learning_states(),'rubrics':current()['rubrics'] if current()['flags'].get('rubrics',True) else [],'custom_fields':current()['custom_fields'],'draft_values':dict(request.POST.items()) if request.method=='POST' else {}})

@login_required
@require_POST
def class_save(request,pk):
    obj=get_object_or_404(session_q(request.user),pk=pk)
    try:
        with transaction.atomic():
            expected=int(request.POST.get('version','0'))
            if obj.version!=expected: raise ValidationError('La sesión ha cambiado. Recarga antes de guardar.')
            if obj.status in ('cancelled','recover'): raise ValidationError('No puedes registrar una sesión cancelada o pendiente de recuperar.')
            day=timezone.localtime(obj.start).date()
            roster=Student.objects.filter(enrollments__group=obj.group,enrollments__starts__lte=day).filter(Q(enrollments__ends=None)|Q(enrollments__ends__gte=day)).distinct()
            for student in roster:
                key=str(student.pk)
                status=request.POST.get('attendance_'+key,'')
                if status:
                    if status not in dict(Attendance.STATES): raise ValidationError('Estado de asistencia no válido.')
                    Attendance.objects.update_or_create(session=obj,student=student,defaults={'status':status,'note':request.POST.get('note_'+key,'')[:250]})
                if request.POST.get('record_'+key):
                    state=request.POST.get('state_'+key,learning_states()[0][0]); learning_state=request.POST.get('learning_'+key,learning_states()[0][0])
                    if state not in dict(learning_states()) or learning_state not in dict(learning_states()): raise ValidationError('Estado de aprendizaje no válido.')
                    challenge=request.POST.get('challenge_'+key,'').strip() or request.POST.get('common_activity','').strip()
                    if not challenge: raise ValidationError('Indica el reto trabajado para cada registro seleccionado.')
                    rubric={r:request.POST.get('rubric_'+key+'_'+str(n),'')[:200] for n,r in enumerate(current()['rubrics'] if current()['flags'].get('rubrics',True) else [])}
                    previous=Learning.objects.filter(session=obj,student=student).order_by('-created_at').first()
                    Learning.objects.create(session=obj,student=student,author=request.user,challenge=challenge[:200],evidence=request.POST.get('evidence_'+key,''),achievement=request.POST.get('achievement_'+key,''),difficulty=request.POST.get('difficulty_'+key,''),objective=request.POST.get('objective_'+key,''),support=request.POST.get('support_'+key,''),student_comment=request.POST.get('comment_'+key,''),next_step=request.POST.get('next_'+key,''),internal_notes=request.POST.get('private_'+key,''),activity_status=state,learning_status=learning_state,rubric=rubric,supersedes=previous)
            values={k:request.POST.get(k,'') for k in ('actual','pending','adaptations','notes','next_steps')}
            values['status']='done' if request.POST.get('close') else obj.status
            if values['status']=='done' and not values['actual'].strip(): raise ValidationError('Describe lo realizado antes de cerrar la sesión.')
            if not Session.objects.filter(pk=obj.pk,version=expected).update(**values,version=expected+1,updated_at=timezone.now()): raise ValidationError('Conflicto de edición. Recarga y vuelve a intentarlo.')
            audit(request.user,'session:close' if request.POST.get('close') else 'session:draft',obj)
        messages.success(request,'Clase guardada. Los registros individuales conservan sus versiones anteriores.')
    except (ValidationError,ValueError) as e:
        messages.error(request,' '.join(e.messages) if isinstance(e,ValidationError) else 'Versión no válida.')
        response=session_detail(request,pk); response.status_code=422; return response
    return redirect('session',pk=pk)

@login_required
def recover_session(request,pk):
    source=get_object_or_404(session_q(request.user),pk=pk)
    if source.status not in ('recover','cancelled'): return HttpResponse('Solo se recuperan sesiones canceladas o pendientes.',status=400)
    form=SessionForm(request.POST or None,initial={k:getattr(source,k) for k in ['group','teacher','title','number','resource','goals','materials','planned']})
    form.fields['group'].queryset=groups(request.user)
    form.fields['teacher'].queryset=User.objects.filter(classgroup__in=groups(request.user)).distinct()
    if request.method=='POST' and form.is_valid():
        try:
            obj=form.save(commit=False); obj.recovery_of=source; obj.resource_snapshot=source.resource_snapshot
            session_errors(obj); obj.save(); audit(request.user,'session:recover',obj); return redirect('session',pk=obj.pk)
        except ValidationError as e: fail(form,e)
    return render(request,'core/form.html',{'title':'Recuperar sesión · se conserva la original','form':form})

@login_required
def evidence_add(request,pk):
    student=get_object_or_404(students(request.user),pk=pk)
    form=EvidenceForm(request.POST or None,request.FILES or None)
    form.fields['session'].queryset=session_q(request.user).filter(group__enrollments__student=student).distinct()
    if request.method=='POST' and form.is_valid():
        upload=form.cleaned_data.get('file')
        error=None
        if not upload and not form.cleaned_data.get('url'): error='Adjunta un archivo o un enlace.'
        if upload:
            head=upload.read(16); upload.seek(0)
            ext=Path(upload.name).suffix.lower()
            allowed=(ext=='.pdf' and head.startswith(b'%PDF-')) or (ext=='.png' and head.startswith(b'\x89PNG\r\n\x1a\n')) or (ext in ('.jpg','.jpeg') and head.startswith(b'\xff\xd8\xff'))
            if not allowed or upload.size>10*1024*1024: error='Solo PDF, PNG o JPEG verificados, hasta 10 MB. Los archivos se descargan de forma privada.'
            elif ext in ('.png','.jpg','.jpeg'):
                try:
                    from PIL import Image
                    im=Image.open(upload); im.verify(); upload.seek(0)
                except Exception: error='Imagen inválida.'
            if not error: upload.name=str(uuid.uuid4())+ext
        if error: form.add_error(None,error)
        else:
            obj=form.save(commit=False); obj.student=student; obj.author=request.user; obj.save(); audit(request.user,'evidence:create',obj)
            return redirect(reverse('student',args=[pk])+'?tab=evidence')
    return render(request,'core/form.html',{'title':'Añadir evidencia privada','form':form})

@login_required
def evidence_download(request,pk):
    evidence=get_object_or_404(Evidence,pk=pk,student__in=students(request.user),session__group__in=groups(request.user))
    if not evidence.file: return HttpResponse(status=404)
    audit(request.user,'evidence:download',evidence)
    response=FileResponse(evidence.file.open('rb'),as_attachment=True,filename='evidencia'+Path(evidence.file.name).suffix)
    response['Cache-Control']='no-store'; return response

@login_required
def reports(request):
    require_module(request.user,'reports')
    student=None; rows=[]; attendance=[]
    if request.GET.get('student'):
        student=get_object_or_404(students(request.user),pk=request.GET['student'])
        rows=Learning.objects.filter(student=student,session__group__in=groups(request.user)).select_related('session','author').order_by('created_at')
        attendance=Attendance.objects.filter(student=student,session__group__in=groups(request.user)).select_related('session')
        for key,op in [('from','gte'),('to','lte')]:
            if request.GET.get(key):
                try:
                    value=date.fromisoformat(request.GET[key]); rows=rows.filter(**{'session__start__date__'+op:value}); attendance=attendance.filter(**{'session__start__date__'+op:value})
                except ValueError: return HttpResponse('Periodo inválido.',status=400)
        if request.GET.get('group'):
            report_group=get_object_or_404(groups(request.user),pk=request.GET['group'])
            rows=rows.filter(session__group=report_group); attendance=attendance.filter(session__group=report_group)
        if request.GET.get('domain'): rows=rows.filter(session__resource_snapshot__domain=request.GET['domain'])
    sections=request.GET.getlist('section')
    if not sections: sections=['achievement','next_step']
    allowed={'challenge':'Actividades y proyectos','evidence':'Evidencias observadas','achievement':'Avances y fortalezas','support':'Apoyos utilizados','next_step':'Objetivos pendientes y próximos pasos'}
    sections=[s for s in sections if s in allowed]
    report_rows=[{'date':timezone.localtime(r.session.start).strftime('%d/%m/%Y'),'session':r.session.title,'fields':[(allowed[s],getattr(r,s)) for s in sections]} for r in rows]
    if student and request.GET.get('format') in ('pdf','csv'):
        audit(request.user,'report:export',student)
        if request.GET['format']=='csv':
            response=HttpResponse(content_type='text/csv; charset=utf-8'); response['Content-Disposition']='attachment; filename="informe.csv"'
            writer=csv.writer(response); writer.writerow(['Fecha','Sesión']+[allowed[s] for s in sections])
            def safe(v): return "'"+v if v.startswith(('=','+','-','@','\t','\r')) else v
            for row in report_rows: writer.writerow([row['date'],safe(row['session'])]+[safe(v) for _,v in row['fields']])
            return response
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from xml.sax.saxutils import escape
        output=io.BytesIO(); doc=SimpleDocTemplate(output); styles=getSampleStyleSheet()
        body=[Paragraph('Atigra Makers · Informe para familia',styles['Title']),Paragraph(escape(student.name),styles['Heading2']),Paragraph(escape(current()['report_template']),styles['BodyText'])]
        for row in report_rows:
            body.append(Paragraph(escape(row['date']+' · '+row['session']),styles['Heading3']))
            for label,value in row['fields']: body.append(Paragraph(escape(label+': '+value),styles['BodyText']))
            body.append(Spacer(1,12))
        if request.GET.get('attendance'):
            body.append(Paragraph('Asistencia',styles['Heading2']))
            for a in attendance: body.append(Paragraph(escape(str(timezone.localtime(a.session.start).date())+': '+a.get_status_display()),styles['BodyText']))
        doc.build(body); output.seek(0); return FileResponse(output,as_attachment=True,filename='informe-familia.pdf')
    return render(request,'core/reports.html',{'title':'Informes','students':students(request.user),'groups':groups(request.user),'student':student,'report_rows':report_rows,'attendance':attendance if request.GET.get('attendance') else [],'sections':sections,'available_sections':allowed.items(),'domains':Resource.objects.values_list('domain',flat=True).distinct()})

@login_required
def settings_view(request):
    require_admin(request.user)
    return page(request,'Configuración',section='settings',years=AcademicYear.objects.order_by('-starts'),users=User.objects.select_related('profile').order_by('username'),guardians=Guardian.objects.all(),holidays=Holiday.objects.order_by('start'))

@login_required
def admin_form(request,kind,pk=None):
    require_admin(request.user)
    mapping={'year':(YearForm,AcademicYear,'Curso académico'),'guardian':(GuardianForm,Guardian,'Responsable'),'holiday':(HolidayForm,Holiday,'Periodo sin clase')}
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
    return render(request,'core/form.html',{'title':'Crear usuario interno','form':form})

@login_required
def task_add(request):
    def prepare(form): form.instance.author=request.user
    return generic_edit(request,TaskForm,'Recordatorio docente',None,'home',prepare)

@login_required
@require_POST
def task_done(request,pk):
    obj=get_object_or_404(Task,pk=pk,author=request.user); obj.done=True; obj.save(); return redirect('home')

@login_required
def consent_add(request,pk):
    require_admin(request.user); student=get_object_or_404(Student,pk=pk)
    def prepare(form): form.instance.student=student
    return generic_edit(request,ConsentForm,'Registrar autorización específica',None,reverse('student',args=[pk]),prepare)

@login_required
def developer_view(request):
    require_developer(request.user)
    error=''; payload=json.dumps(current(),ensure_ascii=False,indent=2)
    if request.method=='POST':
        payload=request.POST.get('payload','')
        try:
            config=validate_config(json.loads(payload))
            description=request.POST.get('description','').strip()
            if not description: raise ValidationError('Describe el cambio.')
            version=ConfigVersion.objects.create(environment=settings.ENVIRONMENT,author=request.user,description=description[:250],payload=config)
            audit(request.user,'config:draft',version); return redirect('config_preview',pk=version.pk)
        except (ValidationError,json.JSONDecodeError) as e: error=' '.join(e.messages) if isinstance(e,ValidationError) else 'JSON no válido.'
    with connection.cursor() as cursor: cursor.execute('SELECT 1'); db_ok=cursor.fetchone()[0]==1
    return render(request,'core/developer.html',{'title':'Desarrollador','payload':payload,'error':error,'versions':ConfigVersion.objects.filter(environment=settings.ENVIRONMENT).select_related('author').order_by('-created_at'),'audits':Audit.objects.filter(action__startswith='config:').select_related('actor').order_by('-created_at')[:30],'db_ok':db_ok,'backup':BackupCheck.objects.order_by('-created_at').first(),'releases':Release.objects.order_by('-deployed_at'),'app_version':'0.1.0','technical_events':TechnicalEvent.objects.order_by('-created_at')[:20]})

@login_required
def config_preview(request,pk):
    require_developer(request.user)
    obj=get_object_or_404(ConfigVersion,pk=pk,environment=settings.ENVIRONMENT)
    try: config=validate_config(obj.payload)
    except ValidationError as e: return HttpResponse('Configuración inválida: '+' '.join(e.messages),status=400)
    if request.method=='POST':
        if request.POST.get('action')=='validate':
            if obj.state=='draft': obj.state='preview'; obj.save(); audit(request.user,'config:preview',obj)
        elif request.POST.get('action')=='publish':
            if obj.state!='preview' or request.POST.get('confirm')!='PUBLICAR': return HttpResponse('Valida la vista previa y confirma escribiendo PUBLICAR.',status=400)
            with transaction.atomic():
                changed=ConfigVersion.objects.filter(pk=obj.pk,state='preview').update(state='published',published_at=timezone.now())
                if changed: audit(request.user,'config:publish',obj)
            messages.success(request,'Configuración publicada en '+settings.ENVIRONMENT+'.'); return redirect('developer')
    return render(request,'core/preview.html',{'title':'Vista previa aislada','config_version':obj,'preview':config,'preview_json':json.dumps(config,ensure_ascii=False,indent=2)})

@login_required
@require_POST
def config_restore(request,pk):
    require_developer(request.user)
    old=get_object_or_404(ConfigVersion,pk=pk,environment=settings.ENVIRONMENT,state='published')
    if request.POST.get('confirm')!='RESTAURAR': return HttpResponse('Confirma escribiendo RESTAURAR. Solo se restaura configuración; no datos educativos.',status=400)
    version=ConfigVersion.objects.create(environment=settings.ENVIRONMENT,author=request.user,description='Restauración de configuración '+str(old.pk),payload=validate_config(old.payload))
    audit(request.user,'config:restore-draft',version); return redirect('config_preview',pk=version.pk)

@login_required
def user_edit(request,pk):
    require_admin(request.user)
    target=get_object_or_404(User,pk=pk)
    target_profile=profile(target)
    form=EditUserForm(request.POST or None,initial={'first_name':target.first_name,'role':target_profile.role,'active':target.is_active,'sensitive_access':target_profile.sensitive_access,'development_access':target_profile.development_access})
    if request.method=='POST' and form.is_valid():
        if target==request.user and (not form.cleaned_data['active'] or form.cleaned_data['role']!='admin'):
            form.add_error(None,'No puedes quitarte tu propio acceso de administración.')
        else:
            with transaction.atomic():
                target.first_name=form.cleaned_data['first_name']; target.is_active=form.cleaned_data['active']; target.save()
                target_profile.role=form.cleaned_data['role']; target_profile.sensitive_access=form.cleaned_data['sensitive_access']; target_profile.development_access=form.cleaned_data['development_access']; target_profile.save()
                audit(request.user,'user:permissions',target)
            return redirect('settings')
    return render(request,'core/form.html',{'title':'Permisos de '+target.username,'form':form})

@login_required
def group_report(request):
    require_module(request.user,'reports')
    selected=None; progress=Learning.objects.none(); attendance=Attendance.objects.none()
    if request.GET.get('group'):
        selected=get_object_or_404(groups(request.user),pk=request.GET['group'])
        progress=Learning.objects.filter(session__group=selected).select_related('student','session','author').order_by('-session__start','student__name')
        attendance=Attendance.objects.filter(session__group=selected).select_related('student','session').order_by('-session__start','student__name')
        for key,lookup in [('from','gte'),('to','lte')]:
            if request.GET.get(key):
                try: value=date.fromisoformat(request.GET[key])
                except ValueError: return HttpResponse('Fecha no válida.',status=400)
                progress=progress.filter(**{'session__start__date__'+lookup:value}); attendance=attendance.filter(**{'session__start__date__'+lookup:value})
        if request.GET.get('domain'): progress=progress.filter(session__resource_snapshot__domain=request.GET['domain'])
    if request.GET.get('format')=='csv' and selected:
        audit(request.user,'report:group-export',selected)
        output=HttpResponse(content_type='text/csv; charset=utf-8');output['Content-Disposition']='attachment; filename="seguimiento-grupo.csv"'
        writer=csv.writer(output);writer.writerow(['Alumno','Fecha','Sesión','Reto','Aprendizaje','Evidencia','Próximo paso'])
        def safe(value):
            value=str(value)
            return "'"+value if value.startswith(('=','+','-','@','\t','\r')) else value
        for r in progress: writer.writerow([safe(v) for v in [r.student.name,timezone.localtime(r.session.start).date(),r.session.title,r.challenge,r.get_learning_status_display(),r.evidence,r.next_step]])
        return output
    return render(request,'core/group_report.html',{'title':'Seguimiento de grupo','groups':groups(request.user),'selected_group':selected,'progress':progress,'attendance_rows':attendance,'domains':Resource.objects.values_list('domain',flat=True).distinct()})

@login_required
def student_export(request,pk):
    require_admin(request.user)
    student=get_object_or_404(Student,pk=pk)
    if request.method=='POST':
        if request.POST.get('confirm')!='EXPORTAR': return HttpResponse('Confirma el alcance escribiendo EXPORTAR.',status=400)
        include_sensitive=request.POST.get('sensitive')=='1'
        if include_sensitive: require_sensitive(request.user,student)
        from django.forms.models import model_to_dict
        def values(query): return list(query.values())
        data={'student':{f.name:getattr(student,f.name) for f in student._meta.fields},'enrollments':values(student.enrollments.all()),'responsible_links':[{**{f.name:getattr(link,f.attname) for f in link._meta.fields},'guardian':model_to_dict(link.guardian)} for link in student.guardians.select_related('guardian')],'consents':values(student.consents.all()),'learning':values(student.learning.all()),'attendance':values(Attendance.objects.filter(student=student)),'evidence_metadata':values(student.evidences.all())}
        if include_sensitive: data['restricted']=values(student.restricted_notes.all()); audit(request.user,'restricted:export',student)
        audit(request.user,'student:export',student)
        response=JsonResponse(data,json_dumps_params={'ensure_ascii':False,'indent':2});response['Content-Disposition']='attachment; filename="expediente.json"';response['Cache-Control']='no-store';return response
    return page(request,'Exportación administrativa',section='export',student=student,can_sensitive=profile(request.user).sensitive_access)
