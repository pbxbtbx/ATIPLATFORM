from django.conf import settings
from .access import developer, admin
from .configuration import current

def navigation(request):
    config=current()
    destinations={'Inicio':('/','⌂'),'Calendario':('/calendar/','▦'),'Grupos':('/groups/','◫'),'Alumnado':('/students/','◎'),'Biblioteca':('/library/','▤'),'Informes':('/reports/','▥'),'Configuración':('/settings/','⚙')}
    items=[]
    if request.user.is_authenticated:
        for name in config['menus']:
            if name=='Biblioteca' and not config['modules'].get('library',True): continue
            if name=='Informes' and not config['modules'].get('reports',True): continue
            if name=='Configuración' and not admin(request.user): continue
            url,icon=destinations[name]; items.append((config['labels'].get(name,name),url,icon))
    return {'environment':settings.ENVIRONMENT,'ui':config,'nav_items':items,'is_developer':request.user.is_authenticated and developer(request.user),'is_admin':request.user.is_authenticated and admin(request.user)}
