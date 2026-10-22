from django.utils.translation import gettext as _
from django.conf import settings
from .access import developer, admin, profile, educational
from .accessibility import preferences,audio_context
from .configuration import current
from .models import Task
from django.utils import timezone
from .presentation import LEARNING_RARITIES, RARITY_BY_STATUS

def navigation(request):
    config=current()
    notification_tasks=Task.objects.filter(author=request.user,done=False).order_by('due') if request.user.is_authenticated else Task.objects.none()
    destinations={'Inicio':('/','⌂'),'Calendario':('/calendar/','▦'),'Grupos':('/groups/','◫'),'Alumnado':('/students/','◎'),'Biblioteca':('/library/','▤'),'Informes':('/reports/','▥'),'Configuración':('/settings/','⚙')}
    items=[]
    if request.user.is_authenticated:
        for name in config['menus']:
            if name=='Biblioteca' and not config['modules'].get('library',True): continue
            if name=='Informes' and not config['modules'].get('reports',True): continue
            if name=='Configuración' and not admin(request.user): continue
            url,icon=destinations[name]; items.append((config['labels'].get(name,_(name)),url,icon))
    accessibility=preferences(profile(request.user).accessibility if request.user.is_authenticated else {})
    classes=['a11y-text-'+accessibility['text_size'],'a11y-contrast-'+accessibility['contrast']]+['a11y-'+name for name in ('spacing','large_targets','reduce_motion','simple') if accessibility[name]]
    return {'accessibility':accessibility,'accessibility_classes':' '.join(classes),'audio_messages':audio_context(request),'can_practice':request.user.is_authenticated and educational(request.user),'browser_messages':{'unsaved':_('Cambios pendientes de guardar'),'saved':_('Sin cambios pendientes'),'offline':_('Sin conexión. Mantén esta página abierta y guarda al reconectar.'),'unsavedDetails':_('Los cambios de esta página aún no se han guardado.')},'notification_count':notification_tasks.count(),'notification_tasks':notification_tasks[:3],'notification_today':timezone.localdate(),'language_code':getattr(request,'LANGUAGE_CODE','es'),'appearance_theme':profile(request.user).theme if request.user.is_authenticated else 'rpg','learning_palette':profile(request.user).learning_palette if request.user.is_authenticated else 'rpg','learning_rarities':LEARNING_RARITIES,'rarity_by_status':RARITY_BY_STATUS,'environment':settings.ENVIRONMENT,'ui':config,'nav_items':items,'is_developer':request.user.is_authenticated and developer(request.user),'is_admin':request.user.is_authenticated and admin(request.user)}
