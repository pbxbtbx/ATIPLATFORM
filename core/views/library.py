from django.utils.translation import gettext as _
from .common import *

@login_required
def library(request):
    require_module(request.user,'library')
    qs=Resource.objects.order_by('domain','title')
    if request.GET.get('q'): qs=qs.filter(Q(title__icontains=request.GET['q'])|Q(domain__icontains=request.GET['q']))
    return page(request,_('Biblioteca maker'),resources=qs,section='library',sequences=Sequence.objects.filter(group__in=groups(request.user)))


@login_required
def resource_edit(request,pk=None):
    require_module(request.user,'library')
    return generic_edit(request,ResourceForm,_('Recurso de aprendizaje'),get_object_or_404(Resource,pk=pk) if pk else None,'library')


@login_required
def sequence_edit(request):
    require_module(request.user,'library')
    form=SequenceForm(request.POST or None); form.fields['group'].queryset=groups(request.user)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False); obj.snapshot=[snapshot(r) for r in form.cleaned_data['resources']]; obj.save(); form.save_m2m(); audit(request.user,'sequence:create',obj)
        return redirect('library')
    return render(request,'core/form.html',{'title':_('Asignar secuencia (copia histórica)'),'form':form})

