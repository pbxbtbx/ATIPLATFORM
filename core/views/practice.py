from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import render,redirect
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from core.access import educational,audit
from core.curriculum import AREAS
from core.challenges import tier_for
from core import practice as store


class PracticeForm(forms.Form):
    version=forms.IntegerField(min_value=0,widget=forms.HiddenInput)
    area=forms.ChoiceField(choices=[(a['key'],a['label']) for a in AREAS],widget=forms.HiddenInput)
    reached_alpha=forms.MultipleChoiceField(choices=[(f'R{n}',f'R{n}') for n in range(1,9)],required=False)
    reached_beta=forms.MultipleChoiceField(choices=[(f'R{n}',f'R{n}') for n in range(1,9)],required=False)


@login_required
@never_cache
def practice_view(request):
    if not educational(request.user):raise PermissionDenied
    area=request.GET.get('area','games')
    if area not in store.TASKS:area='games'
    error=''
    if request.method=='POST':
        try:
            if request.POST.get('action')=='reset':
                if request.POST.get('confirm')!='REINICIAR':raise ValidationError(_('Escribe REINICIAR para borrar únicamente tu práctica ficticia.'))
                store.save(request.user.pk,int(request.POST.get('version','-1')),None,None,[],reset=True)
                audit(request.user,'practice:reset');messages.success(request,_('Práctica ficticia reiniciada. Los datos educativos reales se conservan.'))
                return redirect('practice')
            form=PracticeForm(request.POST)
            if form.is_valid():
                values=form.cleaned_data;area=values['area']
                store.save(request.user.pk,values['version'],'both',area,{key:values['reached_'+key] for key,label in store.PUPILS})
                audit(request.user,'practice:save');messages.success(request,_('Retos ficticios guardados en la base de práctica.'))
                return redirect('/practice/?area='+area)
            error=_('Revisa la selección y la versión de la práctica.')
        except (ValidationError,ValueError) as exc:error=' '.join(exc.messages) if isinstance(exc,ValidationError) else _('Versión no válida.')
    version,state=store.read(request.user.pk)
    if error:
        try:version=max(0,int(request.POST.get('version',version)))
        except ValueError:pass
    pupils=[]
    for key,label in store.PUPILS:
        reached=state['students'][key][area]
        if error and request.POST.get('action')!='reset':
            reached=[v for v in request.POST.getlist('reached_'+key) if v in {f'R{n}' for n in range(1,9)}]
        cards=[]
        for definition in AREAS:
            count=len(state['students'][key][definition['key']])
            cards.append({**definition,'count':count,'total':8,'percent':round(count*100/8),'tier':tier_for(count,8),'sessions':1 if count else 0,'observations':0})
        pupils.append({'key':key,'name':label,'reached':reached,'count':len(reached),'tier':tier_for(len(reached),8),'board':cards})
    response=render(request,'core/practice.html',{'title':_('Práctica ficticia'),'area':area,'areas':AREAS,'pupils':pupils,'version':version,'error':error,'tasks':[{'id':f'R{n+1}','title':task} for n,task in enumerate(store.TASKS[area])],'practice_mode':True})
    if error:response.status_code=422
    return response
