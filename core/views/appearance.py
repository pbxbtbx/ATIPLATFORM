from django.utils.translation import gettext as _
from .common import *

@login_required
def appearance(request):
    user_profile=profile(request.user)
    form=AppearanceForm(request.POST or None,initial={'theme':user_profile.theme})
    if request.method=='POST' and form.is_valid():
        user_profile.theme=form.cleaned_data['theme']
        user_profile.save(update_fields=['theme'])
        audit(request.user,'appearance:update',user_profile)
        messages.success(request,_('Tu estilo se ha guardado. Solo cambia la apariencia de tu cuenta.'))
        return redirect('appearance')
    return render(request,'core/appearance.html',{'title':_('Personalización'),'form':form})

