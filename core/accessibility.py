"""Preferencias de interfaz acotadas y ayudas de voz sin contenido personal."""
from django import forms
from django.utils.translation import gettext_lazy as _

DEFAULTS={'text_size':'normal','contrast':'normal','spacing':False,'large_targets':False,'reduce_motion':False,'simple':False,'audio':False,'speech_rate':'1'}


def preferences(raw):
    result=DEFAULTS.copy()
    if not isinstance(raw,dict):return result
    for key,default in DEFAULTS.items():
        value=raw.get(key,default)
        if isinstance(default,bool):result[key]=value if isinstance(value,bool) else default
        elif value in {'text_size':('normal','large','extra'),'contrast':('normal','high'),'speech_rate':('0.85','1','1.15')}[key]:result[key]=value
    return result


class AccessibilityForm(forms.Form):
    text_size=forms.ChoiceField(label=_('Tamaño del texto'),choices=[('normal',_('Normal')),('large',_('Grande')),('extra',_('Muy grande'))])
    contrast=forms.ChoiceField(label=_('Contraste'),choices=[('normal',_('Del tema elegido')),('high',_('Alto contraste'))])
    spacing=forms.BooleanField(label=_('Más espacio entre líneas y bloques'),required=False)
    large_targets=forms.BooleanField(label=_('Botones y controles más grandes'),required=False)
    reduce_motion=forms.BooleanField(label=_('Reducir movimiento y animaciones'),required=False)
    simple=forms.BooleanField(label=_('Simplificar decoración de la interfaz'),required=False)
    audio=forms.BooleanField(label=_('Activar ayudas de audiodescripción'),required=False)
    speech_rate=forms.ChoiceField(label=_('Velocidad de lectura'),choices=[('0.85',_('Pausada')),('1',_('Normal')),('1.15',_('Ágil'))])


PAGE_HELP={
 'home':_('Pantalla de inicio. Consulta las clases del día, las sesiones pendientes y tus recordatorios. Usa la navegación para abrir calendario, grupos o alumnado.'),
 'student':_('Ficha individual. Usa las pestañas Resumen, Aprendizaje, Asistencia, Proyectos y evidencias, Tutores e Información restringida, si tienes permiso. En Aprendizaje hay tres bloques principales y dos extras, seguidos del historial.'),
 'session':_('Modo clase. Primero están los materiales y los objetivos, después atención a la diversidad y el mapa de retos. Despliega la fila de cada alumno para registrar asistencia y retos. Guarda los cambios antes de salir.'),
 'accessibility':_('Accesibilidad de la interfaz. Puedes elegir tamaño de texto, contraste, espaciado, controles grandes, movimiento reducido y decoración simplificada. Las ayudas de voz se escuchan solo al pulsar un botón.'),
 'practice':_('Práctica ficticia en una base separada. Hay dos aprendices ficticios y cinco ámbitos. Elige un ámbito, abre un aprendiz y marca sus retos. Dos de ocho dan verde y ocho de ocho dan naranja en la paleta RPG. Guarda para conservar la práctica. No afecta al alumnado real.'),
}
GENERIC_HELP=_('Usa la navegación principal para cambiar de sección. Los títulos separan los bloques de contenido. Tabulador recorre los controles, Enter activa botones y los formularios necesitan guardarse para conservar los cambios.')


def audio_context(request):
    route=getattr(getattr(request,'resolver_match',None),'url_name','')
    return {'pageHelp':str(PAGE_HELP.get(route,GENERIC_HELP)),
            'unavailable':str(_('No hay una voz local disponible para este idioma. Puedes instalar una voz local en tu dispositivo o utilizar un lector de pantalla.')),
            'unsupported':str(_('Este navegador no ofrece lectura de voz. Puedes utilizar un lector de pantalla.')),
            'ready':str(_('Voz local preparada. Pulsa Escuchar para comenzar.')),
            'speaking':str(_('Lectura en curso.')),'stopped':str(_('Lectura detenida.')),
            'paused':str(_('Lectura en pausa.')),'finished':str(_('Lectura finalizada.')),
            'sample':str(_('Esta es una prueba de las ayudas de voz de Atigra Makers. Puedes pausar, continuar o detener la lectura.'))}
