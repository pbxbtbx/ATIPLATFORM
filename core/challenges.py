"""Retos estructurados y progreso de actividad; no infiere evaluación ni diagnósticos."""
import math
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def sections(text):
    headings=['Preparar antes de la clase','Estructura de la sesión','Presentación inicial','Ladrillos que trabajamos','Retos desbloqueables','Errores previsibles y respuesta docente','Atención a la diversidad','Plan B','Cierre','Qué observar para el seguimiento']
    result={}; active=None
    for line in text.splitlines():
        line=line.strip()
        if line in headings: active=line;result.setdefault(active,[])
        elif active:result[active].append(line)
    return {k:'\n'.join(v).strip() for k,v in result.items()}


def extract_challenges(text):
    content=sections(text).get('Retos desbloqueables',text)
    lines=content.splitlines(); indices=[i for i,line in enumerate(lines) if re.fullmatch(r'R\d{1,2}',line.strip())]
    result=[]
    for n,start in enumerate(indices):
        end=indices[n+1] if n+1<len(indices) else len(lines)
        values=[v.strip() for v in lines[start+1:end] if v.strip()]
        if not values:continue
        result.append({'id':lines[start].strip(),'title':values[0],'hint':values[1] if len(values)>1 else '', 'criteria':'\n'.join(values[2:])})
    return result[:30]


def specs_for(session):
    if session.challenge_specs or session.resource_snapshot.get('challenges_configured'):return session.challenge_specs
    return extract_challenges(session.resource_snapshot.get('source_text','') or session.planned)


def diversity_for(session):
    return session.diversity or sections(session.resource_snapshot.get('source_text','') or session.planned).get('Atención a la diversidad','') or session.resource_snapshot.get('supports','')


def validate_specs(specs):
    if not isinstance(specs,list) or len(specs)>30:raise ValidationError(_('Máximo 30 retos por sesión.'))
    seen=set()
    for item in specs:
        if not isinstance(item,dict) or set(item)!={'id','title','hint','criteria'}:raise ValidationError(_('Formato de retos no válido.'))
        if not all(isinstance(v,str) for v in item.values()) or not re.fullmatch(r'R[1-9]\d?',item['id']) or not item['title'].strip() or len(item['title'])>500 or any(len(item[k])>2000 for k in ('hint','criteria')) or item['id'] in seen:
            raise ValidationError(_('Cada reto necesita un identificador único y una consigna válida.'))
        seen.add(item['id'])


def tier_for(count,total):
    if total and count==total:return 'legendary'
    if total and count>=math.ceil(total*.75):return 'epic'
    if total and count>=math.ceil(total*.5):return 'rare'
    if total and count>=math.ceil(total*.25):return 'uncommon'
    return 'common'


def progress_for(session,student,specs):
    from .models import ChallengeProgress
    latest=ChallengeProgress.objects.filter(session=session,student=student).order_by('-created_at','-id').first()
    reached=latest.reached if latest else []
    count=len(set(reached)&{s['id'] for s in specs})
    return {'latest':latest,'reached':reached,'count':count,'total':len(specs),'tier':tier_for(count,len(specs))}


def save_progress(session,student,user,data):
    from .models import ChallengeProgress
    from .access import audit
    specs=specs_for(session);key=str(student.pk)
    if not specs or data.get('track_'+key)!='1':return
    validate_specs(specs)
    if not session.challenge_specs:
        type(session).objects.filter(pk=session.pk).update(challenge_specs=specs)
        session.challenge_specs=specs
    ids=data.getlist('reached_'+key)
    if len(ids)!=len(set(ids)) or set(ids)-{s['id'] for s in specs}:raise ValidationError(_('Los retos seleccionados no pertenecen a esta sesión.'))
    latest=ChallengeProgress.objects.filter(session=session,student=student).order_by('-created_at','-id').first()
    if data.get('progress_version_'+key,'')!=(str(latest.pk) if latest else ''):raise ValidationError(_('Otra persona ha actualizado los retos. Recarga antes de guardar.'))
    evidence=data.get('challenge_evidence_'+key,'').strip()
    if len(evidence)>2000:raise ValidationError(_('La observación de retos no puede superar 2000 caracteres.'))
    if set(ids)!=set(latest.reached if latest else []) or evidence!=(latest.evidence if latest else ''):
        obj=ChallengeProgress.objects.create(session=session,student=student,author=user,content_area=session.content_area,reached=ids,specs=specs,evidence=evidence,supersedes=latest)
        audit(user,'challenge:revision',obj)


def scale_for(total):
    labels={'common':_('Gris'),'uncommon':_('Verde'),'rare':_('Azul'),'epic':_('Lila'),'legendary':_('Naranja · todos')}
    groups={}
    for count in range(total+1):groups.setdefault(tier_for(count,total),[]).append(count)
    return [{'key':key,'label':labels[key],'range':str(values[0]) if len(values)==1 else f'{values[0]}–{values[-1]}'} for key,values in groups.items()]
