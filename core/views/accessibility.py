from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.utils.translation import gettext as _
from core.access import profile,audit
from core.accessibility import AccessibilityForm,preferences


@login_required
def accessibility_view(request):
    account=profile(request.user)
    form=AccessibilityForm(request.POST or None,initial=preferences(account.accessibility))
    if request.method=='POST' and form.is_valid():
        account.accessibility=form.cleaned_data;account.save(update_fields=['accessibility'])
        audit(request.user,'accessibility:update',account)
        messages.success(request,_('Preferencias de accesibilidad guardadas para tu cuenta.'))
        return redirect('accessibility')
    return render(request,'core/accessibility.html',{'title':_('Accesibilidad'),'form':form})
