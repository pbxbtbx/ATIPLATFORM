from django.utils.translation import gettext as _
import re
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import ConfigVersion
DEFAULT = {'brand':'Atigra Makers','primary':'#cc0b4e','secondary':'#45ae46','font':'system-ui','logo_url':'','modules':{'library':True,'reports':True},'labels':{},'menus':['Inicio','Calendario','Grupos','Alumnado','Biblioteca','Informes','Configuración'],'flags':{'rubrics':True},'progress_states':[{'key':k,'label':v} for k,v in [('new','Sin iniciar'),('progress','En proceso'),('supported','Completado con apoyo'),('autonomous','Completado con autonomía'),('resume','Pendiente de retomar')]],'custom_fields':[],'session_template':'','rubrics':['Comprensión del reto','División en pasos','Herramientas','Programación y depuración','Diseño y prototipado','Creatividad','Autonomía','Colaboración','Explicación de decisiones','Cuidado del material'],'report_template':'Avances y próximos pasos','maintenance':False,'retention_days':730}

def validate_config(data):
    if not isinstance(data,dict): raise ValidationError(_('La configuración debe ser un objeto JSON.'))
    if set(data)-set(DEFAULT): raise ValidationError(_('Hay claves no admitidas. No se permite código ejecutable.'))
    result = {**DEFAULT,**data}
    for key in ('primary','secondary'):
        if not isinstance(result[key],str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',result[key]): raise ValidationError(_('Color hexadecimal no válido.'))
    if result['font'] not in ('system-ui','Arial','Georgia','Verdana'): raise ValidationError(_('Tipografía no permitida.'))
    for k in ('brand','logo_url','session_template','report_template'):
        if not isinstance(result[k],str) or len(result[k])>5000: raise ValidationError(_('Texto no válido.'))
    if result['logo_url'] and not result['logo_url'].startswith('/static/'): raise ValidationError(_('El logotipo debe ser un recurso oficial local bajo /static/.'))
    if not isinstance(result['maintenance'],bool): raise ValidationError(_('Mantenimiento debe ser booleano.'))
    if type(result['retention_days']) is not int or not 30<=result['retention_days']<=3650: raise ValidationError(_('Conservación: entre 30 y 3650 días, sujeta a revisión antes de datos reales.'))
    for k in ('modules','flags'):
        if not isinstance(result[k],dict) or any(not isinstance(v,bool) for v in result[k].values()): raise ValidationError(_('Módulos e indicadores deben ser booleanos.'))
    if set(result['modules'])-{'library','reports'}: raise ValidationError(_('Módulo desconocido.'))
    if not isinstance(result['menus'],list) or sorted(result['menus'])!=sorted(DEFAULT['menus']): raise ValidationError(_('Menús debe contener cada sección una vez.'))
    if not isinstance(result['labels'],dict) or any(not isinstance(k,str) or not isinstance(v,str) or len(v)>500 for k,v in result['labels'].items()): raise ValidationError(_('Etiquetas no válidas.'))
    if not isinstance(result['rubrics'],list) or any(not isinstance(x,str) or len(x)>150 for x in result['rubrics']) or len(result['rubrics'])>30: raise ValidationError(_('Rúbricas no válidas.'))
    if not isinstance(result['custom_fields'],list) or len(result['custom_fields'])>30: raise ValidationError(_('Campos no válidos.'))
    for field in result['custom_fields']:
        if not isinstance(field,dict) or set(field)!={'key','label','type','required','options'}: raise ValidationError(_('Cada campo necesita key, label, type, required, options.'))
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',str(field['key'])) or field['type'] not in ('text','choice') or not isinstance(field['required'],bool) or not isinstance(field['label'],str) or not isinstance(field['options'],list) or any(not isinstance(x,str) for x in field['options']): raise ValidationError(_('Definición de campo inválida.'))
    states=result['progress_states']
    if not isinstance(states,list) or not 1<=len(states)<=20: raise ValidationError(_('Debe haber entre 1 y 20 estados de progreso.'))
    for state in states:
        if not isinstance(state,dict) or set(state)!={'key','label'} or not re.fullmatch(r'[a-z][a-z0-9_]{0,19}',str(state['key'])) or not isinstance(state['label'],str) or not 1<=len(state['label'])<=100: raise ValidationError(_('Estado de progreso inválido.'))
    if len({s['key'] for s in states})!=len(states): raise ValidationError(_('Estados de progreso duplicados.'))
    if len({f['key'] for f in result['custom_fields']})!=len(result['custom_fields']): raise ValidationError(_('Identificadores de campo duplicados.'))
    return result

def current():
    v = ConfigVersion.objects.filter(environment=settings.ENVIRONMENT,state='published').order_by('-published_at').first()
    return {**DEFAULT,**(v.payload if v else {})}

def learning_states(): return [(s['key'],s['label']) for s in current()['progress_states']]
