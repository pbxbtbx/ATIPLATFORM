from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import QueryDict
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from django.utils.translation import gettext as _
from core.access import require_admin,audit
from core.import_forms import ODSImportForm
from core.models import ImportDraft,Student,ClassGroup
from core.ods_service import build_plan,commit_plan,plan_fingerprint


def options_data(options):
    data=QueryDict('',mutable=True)
    for key,value in options.items():
        if isinstance(value,list):data.setlist(key,value)
        else:data[key]=value
    return data


def form_context(form,draft):
    selected=set(form['rows'].value() or [])
    sheets=[]
    for sheet in draft.payload['sheets']:
        items=[]
        for row in draft.payload['rows']:
            if row['sheet']!=sheet['id']:continue
            contacts=[]
            for n,source in enumerate(row['contacts']):
                prefix=f"contact_{row['id']}_{n}_"
                contact={key:form[prefix+key] for key in ('include','distinct','name','email','phone')}
                contact['missing_name']=not str(form[prefix+'name'].value() or '').strip()
                contacts.append(contact)
            items.append({'source':row,'selected':row['id'] in selected,'name':form['name_'+row['id']],'birth':form['birth_'+row['id']],'student':form['student_'+row['id']],'contacts':contacts})
        sheet_groups=[form['group_'+str(n)] for n,g in enumerate(draft.payload['groups']) if g['sheet']==sheet['id']]
        has_errors=any(field.errors for item in items for field in [item['name'],item['birth'],item['student']]+[f for c in item['contacts'] for k,f in c.items() if k!='missing_name'])
        sheets.append({'source':sheet,'rows':items,'groups':sheet_groups,'has_errors':has_errors})
    return sheets


@login_required
def ods_preview(request,pk):
    require_admin(request.user)
    draft=get_object_or_404(ImportDraft,pk=pk,author=request.user,kind='ods')
    if draft.created_at<timezone.now()-timedelta(days=1):
        draft.delete();messages.error(request,_('El borrador ha caducado. Vuelve a importar el archivo.'));return redirect('import_start')
    if draft.committed:
        response=render(request,'core/import_preview.html',{'title':_('Importación completada'),'draft':draft})
        response['Cache-Control']='no-store';return response
    confirming=request.method=='POST' and request.POST.get('action')=='confirm'
    reviewed_options=draft.payload.get('options',{})
    data=options_data(reviewed_options) if confirming else request.POST if request.method=='POST' else None
    form=ODSImportForm(data,payload=draft.payload)
    plan=None;reviewed=False
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():
                locked=ImportDraft.objects.select_for_update().get(pk=pk,author=request.user)
                if locked.committed:return redirect('ods_preview',pk=pk)
                if confirming and (not reviewed_options or reviewed_options!=locked.payload.get('options')):raise ValidationError(_('Revisa la vista previa antes de confirmar.'))
                plan=build_plan(locked,form)
                fingerprint=plan_fingerprint(plan)
                if confirming:
                    if fingerprint!=locked.payload.get('fingerprint'):raise ValidationError(_('Los datos han cambiado desde la revisión. Valida de nuevo antes de confirmar.'))
                    commit_plan(plan,request.user)
                    locked.results=[{'id':str(s.pk),'name':str(s)} for s in plan['students']]
                    locked.committed=True;locked.payload={};locked.save()
                    audit(request.user,'import:ods_commit',locked)
                    messages.success(request,_('Alumnado, matrículas y responsables importados. Los registros anteriores se conservan.'))
                    return redirect('ods_preview',pk=pk)
                locked.payload['options']={name:request.POST.getlist(name) if name in ('rows','sheets') else request.POST.get(name,'') for name in form.fields}
                locked.payload['fingerprint']=fingerprint;locked.save(update_fields=['payload'])
                draft=locked;reviewed=True
        except ValidationError as exc:form.add_error(None,exc)
        except ImportDraft.DoesNotExist:
            messages.error(request,_('El borrador ha caducado. Vuelve a importar el archivo.'));return redirect('import_start')
        except (Student.DoesNotExist,ClassGroup.DoesNotExist):form.add_error(None,_('Los datos han cambiado desde la revisión. Valida de nuevo antes de confirmar.'))
    response=render(request,'core/ods_preview.html',{'title':_('Revisar hoja de alumnado ODS'),'draft':draft,'form':form,'sheets':form_context(form,draft),'plan':plan,'reviewed':reviewed})
    response['Cache-Control']='no-store';return response
