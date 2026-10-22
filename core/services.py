from django.utils.translation import gettext as _
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.models import model_to_dict
from django.utils import timezone
from .models import *
from .access import audit

def snapshot(resource):
    if not resource: return {}
    return {k:str(v) for k,v in model_to_dict(resource,exclude=['id','created_at','updated_at']).items()}

def session_errors(session, exclude=None):
    if session.end<=session.start: raise ValidationError(_('El final debe ser posterior al inicio.'))
    local=timezone.localtime(session.start).date()
    if not session.group.starts<=local<=session.group.ends: raise ValidationError(_('La fecha está fuera de la vigencia del grupo.'))
    if not session.group.teachers.filter(pk=session.teacher_id).exists(): raise ValidationError(_('El docente debe estar asignado al grupo.'))
    if session.status not in ('cancelled','recover'):
        if Holiday.objects.filter(start__lte=timezone.localtime(session.end).date(),end__gte=local).exists(): raise ValidationError(_('La sesión coincide con un periodo sin clase.'))
        overlapping=Session.objects.exclude(status__in=['cancelled','recover']).filter(start__lt=session.end,end__gt=session.start)
        if exclude: overlapping=overlapping.exclude(pk=exclude)
        if overlapping.filter(models.Q(group=session.group)|models.Q(teacher=session.teacher)).exists(): raise ValidationError(_('Conflicto: el grupo o docente ya tiene otra clase a esa hora.'))

def save_versioned(form,user):
    obj=form.save(commit=False)
    if obj._state.adding:
        obj.save(); form.save_m2m()
    else:
        expected=form.cleaned_data.get('expected_version')
        fields={f.attname:getattr(obj,f.attname) for f in obj._meta.concrete_fields if not f.primary_key and f.name not in ('created_at','updated_at','version')}
        fields.update(version=models.F('version')+1,updated_at=timezone.now())
        if not type(obj).objects.filter(pk=obj.pk,version=expected).update(**fields): raise ValidationError(_('Otra persona ha modificado este registro. Recarga la página antes de guardar para conservar sus cambios.'))
        form.save_m2m(); obj.refresh_from_db()
    audit(user,'update:'+obj._meta.model_name,obj)
    return obj

@transaction.atomic
def move_student(student,group,date,user,previous=None):
    if group.status!='active': raise ValidationError(_('El grupo de destino debe estar activo.'))
    if not group.starts<=date<=group.ends: raise ValidationError(_('La matrícula debe estar dentro de la vigencia del grupo.'))
    if Enrollment.objects.filter(group=group,ends=None).count()>=group.capacity: raise ValidationError(_('El grupo ha alcanzado su capacidad.'))
    if Enrollment.objects.filter(student=student,group=group,ends=None).exists(): raise ValidationError(_('Ya existe una matrícula activa en este grupo.'))
    if previous:
        old=Enrollment.objects.select_for_update().get(pk=previous,student=student,ends=None)
        if date<old.starts: raise ValidationError(_('El traslado no puede preceder a la matrícula.'))
        old.ends=date-timedelta(days=1); old.save()
    enrollment=Enrollment.objects.create(student=student,group=group,starts=date)
    audit(user,'enrollment:transfer' if previous else 'enrollment:create',enrollment)
    return enrollment
