"""Ámbitos explícitos; los registros conservan su clasificación histórica."""
from django.utils.translation import gettext_lazy as _

AREAS=[
 {'key':'design_3d','label':_('Diseño e impresión 3D'),'icon':'cube','extra':False,'description':_('Diseñar, modelar, prototipar y preparar creaciones para impresión 3D.')},
 {'key':'robotics','label':_('Robótica'),'icon':'robot','extra':False,'description':_('Construir mecanismos y trabajar con sensores, actuadores y automatismos.')},
 {'key':'games','label':_('Programación de videojuegos'),'icon':'game','extra':False,'description':_('Crear juegos, programar sus reglas y probar soluciones.')},
 {'key':'ethical_ai','label':_('IA ética'),'icon':'spark','extra':True,'description':_('Comprender límites, sesgos, privacidad y uso responsable de la inteligencia artificial.')},
 {'key':'mobile_apps','label':_('Creación de apps móviles'),'icon':'phone','extra':True,'description':_('Diseñar interfaces y crear aplicaciones móviles con una finalidad útil.')},
]
AREA_CHOICES=[('',_('Sin bloque asignado'))]+[(a['key'],a['label']) for a in AREAS]


def board(learning,progress):
    from .challenges import tier_for
    learning=list(learning);progress=list(progress)
    superseded={r.supersedes_id for r in learning if r.supersedes_id}
    latest_learning=[r for r in learning if r.pk not in superseded]
    seen=set();latest_progress=[]
    for entry in sorted(progress,key=lambda x:(x.created_at,str(x.pk)),reverse=True):
        if entry.session_id not in seen:latest_progress.append(entry);seen.add(entry.session_id)
    result=[]
    for area in AREAS:
        observations=[r for r in latest_learning if r.content_area==area['key']]
        tracked=[r for r in latest_progress if r.content_area==area['key']]
        reached=sum(len(set(r.reached)&{s['id'] for s in r.specs}) for r in tracked)
        total=sum(len(r.specs) for r in tracked)
        result.append({**area,'observations':len(observations),'sessions':len({r.session_id for r in observations+tracked}),
                       'count':reached,'total':total,'percent':round(100*reached/total) if total else 0,'tier':tier_for(reached,total)})
    return result
