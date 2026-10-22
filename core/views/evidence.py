from django.utils.translation import gettext as _
from .common import *

@login_required
def evidence_add(request,pk):
    student=get_object_or_404(students(request.user),pk=pk)
    form=EvidenceForm(request.POST or None,request.FILES or None)
    form.fields['session'].queryset=session_q(request.user).filter(group__enrollments__student=student).distinct()
    if request.method=='POST' and form.is_valid():
        upload=form.cleaned_data.get('file')
        error=None
        if not upload and not form.cleaned_data.get('url'): error=_('Adjunta un archivo o un enlace.')
        if upload:
            head=upload.read(16); upload.seek(0)
            ext=Path(upload.name).suffix.lower()
            allowed=(ext=='.pdf' and head.startswith(b'%PDF-')) or (ext=='.png' and head.startswith(b'\x89PNG\r\n\x1a\n')) or (ext in ('.jpg','.jpeg') and head.startswith(b'\xff\xd8\xff'))
            if not allowed or upload.size>10*1024*1024: error=_('Solo PDF, PNG o JPEG verificados, hasta 10 MB. Los archivos se descargan de forma privada.')
            elif ext in ('.png','.jpg','.jpeg'):
                try:
                    from PIL import Image
                    im=Image.open(upload); im.verify(); upload.seek(0)
                except Exception: error=_('Imagen inválida.')
            if not error: upload.name=str(uuid.uuid4())+ext
        if error: form.add_error(None,error)
        else:
            obj=form.save(commit=False); obj.student=student; obj.author=request.user; obj.save(); audit(request.user,'evidence:create',obj)
            return redirect(reverse('student',args=[pk])+'?tab=evidence')
    return render(request,'core/form.html',{'title':_('Añadir evidencia privada'),'form':form})


@login_required
def evidence_download(request,pk):
    evidence=get_object_or_404(Evidence,pk=pk,student__in=students(request.user),session__group__in=groups(request.user))
    if not evidence.file: return HttpResponse(status=404)
    audit(request.user,'evidence:download',evidence)
    response=FileResponse(evidence.file.open('rb'),as_attachment=True,filename='evidencia'+Path(evidence.file.name).suffix)
    response['Cache-Control']='no-store'; return response
