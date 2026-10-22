from datetime import date, datetime, timedelta
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import gettext as _
from core.access import admin, educational, require_admin, audit, groups
from core.models import ImportDraft, Student, Session, ClassGroup
from core.import_forms import UploadImportForm, ImportOptionsForm
from core.importing import parse_csv, parse_docx, read_upload
from core.services import move_student, session_errors


def permitted(user,kind):
    if kind in ('students','ods'): require_admin(user)
    elif not educational(user): raise PermissionDenied


def candidates(draft, options):
    """Revalida contra el estado actual; nunca actualiza alumnos ni sesiones existentes."""
    group=options['group']
    if not groups(draft.author).filter(pk=group.pk,status='active').exists(): raise PermissionDenied
    result=[]
    seen=set()
    for row in draft.payload['rows']:
        if draft.kind=='students':
            name=row.get('nombre','').strip()
            key=' '.join(name.casefold().split())
            if not key or key in seen or any(' '.join(n.casefold().split())==key for n in Student.objects.values_list('name',flat=True)):
                raise ValidationError(_('Hay nombres vacíos o repetidos. Revisa la lista; no se fusionan alumnos automáticamente.'))
            seen.add(key)
            try: born=date.fromisoformat(row['nacimiento']) if row.get('nacimiento') else None
            except ValueError: raise ValidationError(_('Fecha de nacimiento no válida: utiliza AAAA-MM-DD.'))
            obj=Student(name=name,preferred_name=row.get('nombre_preferido',''),birth_date=born,joined=options['joined'])
            if born and born>obj.joined: raise ValidationError(_('El nacimiento no puede ser posterior a la incorporación.'))
        else:
            if draft.kind=='word':
                start=options['start']; duration=options['duration']; title=options['title']; number=options['number']
                content={key:options[key] for key in ('goals','materials','diversity','planned')}
            else:
                try:
                    start=datetime.fromisoformat(row['inicio'])
                    if start.tzinfo is None: start=forms.DateTimeField().clean(row['inicio'])
                    duration=int(row['duracion_minutos']); number=int(row.get('numero') or 1)
                except (ValueError,ValidationError): raise ValidationError(_('Inicio, duración o número no válidos en el CSV.'))
                title=row['titulo']; content={'goals':row.get('objetivos',''),'materials':row.get('materiales',''),'planned':row.get('actividades','')}
            if not 1<=duration<=720 or number<1: raise ValidationError(_('Duración o número de sesión fuera de rango.'))
            obj=Session(group=group,teacher=options['teacher'],content_area=options.get('content_area',''),title=title,number=number,start=start,end=start+timedelta(minutes=duration),**content)
            session_errors(obj)
            if any(s.start<obj.end and s.end>obj.start for s in result): raise ValidationError(_('Las sesiones del archivo se solapan entre sí.'))
            from core.challenges import extract_challenges,validate_specs
            obj.challenge_specs=extract_challenges(obj.planned) or extract_challenges(draft.payload.get('source',''))
            validate_specs(obj.challenge_specs)
            obj.resource_snapshot={'import_draft':str(draft.pk),'source_text':draft.payload.get('source','')}
        obj.full_clean()
        result.append(obj)
    if draft.kind=='students':
        from core.models import Enrollment
        if not group.starts<=options['joined']<=group.ends: raise ValidationError(_('La matrícula debe estar dentro de la vigencia del grupo.'))
        if Enrollment.objects.filter(group=group,ends=None).count()+len(result)>group.capacity: raise ValidationError(_('No hay plazas suficientes para todo el lote.'))
    return result


@login_required
def import_start(request):
    if not educational(request.user): raise PermissionDenied
    form=UploadImportForm(request.POST or None,request.FILES or None)
    if not admin(request.user): form.fields['kind'].choices=[choice for choice in form.fields['kind'].choices if choice[0] not in ('students','ods')]
    if request.method=='POST' and form.is_valid():
        kind=form.cleaned_data['kind']; permitted(request.user,kind)
        try:
            upload=form.cleaned_data.get('file')
            initial={}; source=''
            if upload:
                suffix=upload.name.lower().rsplit('.',1)[-1]
                expected={'word':'docx','ods':'ods'}.get(kind,'csv')
                if suffix!=expected: raise ValidationError(_('El formato del archivo no coincide con el tipo de importación seleccionado.'))
                data=read_upload(upload)
                if kind=='ods':
                    from core.ods_importing import parse_ods
                    ods_payload=parse_ods(data);rows=ods_payload['rows']
                elif kind=='word':
                    initial=parse_docx(data); source=initial.pop('source'); rows=[{}]
                else: rows=parse_csv(data,kind)
            else:
                rows=[{'nombre':n.strip()} for n in form.cleaned_data['names'].splitlines() if n.strip()]
                if not 1<=len(rows)<=200: raise ValidationError(_('El límite es de 200 registros por importación.'))
            # Borradores privados, no se conserva el archivo original ni sus metadatos personales.
            ImportDraft.objects.filter(author=request.user,created_at__lt=timezone.now()-timedelta(days=1)).delete()
            draft=ImportDraft.objects.create(author=request.user,kind=kind,payload=ods_payload if kind=='ods' else {'rows':rows,'initial':initial,'source':source})
            audit(request.user,'import:draft',draft)
            return redirect('import_preview',pk=draft.pk)
        except ValidationError as exc: form.add_error(None,exc)
    response=render(request,'core/import_start.html',{'title':_('Importar y añadir en lote'),'form':form})
    response['Cache-Control']='no-store'
    return response


@login_required
def import_preview(request,pk):
    draft=get_object_or_404(ImportDraft,pk=pk,author=request.user)
    permitted(request.user,draft.kind)
    if draft.kind=='ods':return redirect('ods_preview',pk=pk)
    if draft.created_at<timezone.now()-timedelta(days=1):
        draft.delete(); messages.error(request,_('El borrador ha caducado. Vuelve a importar el archivo.')); return redirect('import_start')
    if draft.committed:
        response=render(request,'core/import_preview.html',{'title':_('Importación completada'),'draft':draft})
        response['Cache-Control']='no-store'
        return response
    confirming=request.method=='POST' and request.POST.get('action')=='confirm'
    data=draft.payload.get('options') if confirming else request.POST if request.method=='POST' else None
    form=ImportOptionsForm(data,user=request.user,kind=draft.kind,initial=draft.payload.get('initial',{}))
    reviewed=False; objects=[]
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                draft=ImportDraft.objects.select_for_update().get(pk=pk,author=request.user)
                if draft.committed: return redirect('import_preview',pk=pk)
                if confirming and data != draft.payload.get('options'):
                    raise ValidationError(_('Revisa la vista previa antes de confirmar.'))
                form.cleaned_data['group']=ClassGroup.objects.select_for_update().get(pk=form.cleaned_data['group'].pk)
                objects=candidates(draft,form.cleaned_data)
                if confirming:
                    if not draft.payload.get('options'): raise ValidationError(_('Revisa la vista previa antes de confirmar.'))
                    for obj in objects:
                        obj.save()
                        if draft.kind=='students': move_student(obj,form.cleaned_data['group'],obj.joined,request.user)
                        audit(request.user,'import:create',obj)
                    draft.results=[{'id':str(obj.pk),'name':str(obj)} for obj in objects]
                    draft.committed=True
                    # Minimización: elimina las copias de datos del borrador tras guardar.
                    draft.payload={}; draft.save()
                    audit(request.user,'import:commit',draft)
                    messages.success(request,_('Importación completada. No se han modificado registros anteriores.'))
                    return redirect('import_preview',pk=pk)
                draft.payload['options']={k:v for k,v in request.POST.items() if k in form.fields}
                draft.save(update_fields=['payload']); reviewed=True
        except ValidationError as exc: form.add_error(None,exc)
    response=render(request,'core/import_preview.html',{'title':_('Revisar importación'),'draft':draft,'form':form,'reviewed':reviewed,'objects':objects})
    response['Cache-Control']='no-store'
    return response


@login_required
def import_template(request,kind):
    if kind not in ('students','sessions'): raise PermissionDenied
    permitted(request.user,kind)
    headers='nombre;nombre_preferido;nacimiento\n' if kind=='students' else 'titulo;inicio;duracion_minutos;numero;objetivos;materiales;actividades\n'
    response=HttpResponse('\ufeff'+headers,content_type='text/csv; charset=utf-8')
    response['Content-Disposition']=f'attachment; filename="{kind}.csv"'
    return response
