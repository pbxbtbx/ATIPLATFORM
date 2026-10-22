from django.utils.translation import gettext as _
from .common import *

@login_required
def developer_view(request):
    require_developer(request.user)
    error=''; payload=json.dumps(current(),ensure_ascii=False,indent=2)
    if request.method=='POST':
        payload=request.POST.get('payload','')
        try:
            config=validate_config(json.loads(payload))
            description=request.POST.get('description','').strip()
            if not description: raise ValidationError(_('Describe el cambio.'))
            version=ConfigVersion.objects.create(environment=settings.ENVIRONMENT,author=request.user,description=description[:250],payload=config)
            audit(request.user,'config:draft',version); return redirect('config_preview',pk=version.pk)
        except (ValidationError,json.JSONDecodeError) as e: error=' '.join(e.messages) if isinstance(e,ValidationError) else _('JSON no válido.')
    with connection.cursor() as cursor: cursor.execute('SELECT 1'); db_ok=cursor.fetchone()[0]==1
    return render(request,'core/developer.html',{'title':_('Desarrollador'),'payload':payload,'error':error,'versions':ConfigVersion.objects.filter(environment=settings.ENVIRONMENT).select_related('author').order_by('-created_at'),'audits':Audit.objects.filter(action__startswith='config:').select_related('actor').order_by('-created_at')[:30],'db_ok':db_ok,'backup':BackupCheck.objects.order_by('-created_at').first(),'releases':Release.objects.order_by('-deployed_at'),'app_version':'0.3.0','technical_events':TechnicalEvent.objects.order_by('-created_at')[:20]})


@login_required
def config_preview(request,pk):
    require_developer(request.user)
    obj=get_object_or_404(ConfigVersion,pk=pk,environment=settings.ENVIRONMENT)
    try: config=validate_config(obj.payload)
    except ValidationError as e: return HttpResponse(_('Configuración inválida: ')+' '.join(e.messages),status=400)
    if request.method=='POST':
        if request.POST.get('action')=='validate':
            if obj.state=='draft': obj.state='preview'; obj.save(); audit(request.user,'config:preview',obj)
        elif request.POST.get('action')=='publish':
            if obj.state!='preview' or request.POST.get('confirm')!='PUBLICAR': return HttpResponse(_('Valida la vista previa y confirma escribiendo PUBLICAR.'),status=400)
            with transaction.atomic():
                changed=ConfigVersion.objects.filter(pk=obj.pk,state='preview').update(state='published',published_at=timezone.now())
                if changed: audit(request.user,'config:publish',obj)
            messages.success(request,_('Configuración publicada en ')+settings.ENVIRONMENT+'.'); return redirect('developer')
    return render(request,'core/preview.html',{'title':_('Vista previa aislada'),'config_version':obj,'preview':config,'preview_json':json.dumps(config,ensure_ascii=False,indent=2)})


@login_required
@require_POST
def config_restore(request,pk):
    require_developer(request.user)
    old=get_object_or_404(ConfigVersion,pk=pk,environment=settings.ENVIRONMENT,state='published')
    if request.POST.get('confirm')!='RESTAURAR': return HttpResponse(_('Confirma escribiendo RESTAURAR. Solo se restaura configuración; no datos educativos.'),status=400)
    version=ConfigVersion.objects.create(environment=settings.ENVIRONMENT,author=request.user,description=_('Restauración de configuración ')+str(old.pk),payload=validate_config(old.payload))
    audit(request.user,'config:restore-draft',version); return redirect('config_preview',pk=version.pk)
