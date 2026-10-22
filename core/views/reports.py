from django.utils.translation import gettext as _
from .common import *
from core.i18n import configured_text

@login_required
def reports(request):
    require_module(request.user,'reports')
    student=None; rows=[]; attendance=[]
    if request.GET.get('student'):
        student=get_object_or_404(students(request.user),pk=request.GET['student'])
        rows=Learning.objects.filter(student=student,session__group__in=groups(request.user)).select_related('session','author').order_by('created_at')
        attendance=Attendance.objects.filter(student=student,session__group__in=groups(request.user)).select_related('session')
        for key,op in [('from','gte'),('to','lte')]:
            if request.GET.get(key):
                try:
                    value=date.fromisoformat(request.GET[key]); rows=rows.filter(**{'session__start__date__'+op:value}); attendance=attendance.filter(**{'session__start__date__'+op:value})
                except ValueError: return HttpResponse(_('Periodo inválido.'),status=400)
        if request.GET.get('group'):
            report_group=get_object_or_404(groups(request.user),pk=request.GET['group'])
            rows=rows.filter(session__group=report_group); attendance=attendance.filter(session__group=report_group)
        if request.GET.get('domain'): rows=rows.filter(session__resource_snapshot__domain=request.GET['domain'])
    sections=request.GET.getlist('section')
    if not sections: sections=['achievement','next_step']
    allowed={'challenge':_('Actividades y proyectos'),'evidence':_('Evidencias observadas'),'achievement':_('Avances y fortalezas'),'support':_('Apoyos utilizados'),'next_step':_('Objetivos pendientes y próximos pasos')}
    sections=[s for s in sections if s in allowed]
    report_rows=[{'date':timezone.localtime(r.session.start).strftime('%d/%m/%Y'),'session':r.session.title,'fields':[(allowed[s],getattr(r,s)) for s in sections]} for r in rows]
    if student and request.GET.get('format') in ('pdf','csv'):
        audit(request.user,'report:export',student)
        if request.GET['format']=='csv':
            response=HttpResponse(content_type='text/csv; charset=utf-8'); response['Content-Disposition']='attachment; filename="informe.csv"'
            writer=csv.writer(response); writer.writerow([_('Fecha'),_('Sesión')]+[allowed[s] for s in sections])
            def safe(v): return "'"+v if v.startswith(('=','+','-','@','\t','\r')) else v
            for row in report_rows: writer.writerow([row['date'],safe(row['session'])]+[safe(v) for _,v in row['fields']])
            return response
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from xml.sax.saxutils import escape
        output=io.BytesIO(); doc=SimpleDocTemplate(output); styles=getSampleStyleSheet()
        body=[Paragraph(_('Atigra Makers · Informe para familia'),styles['Title']),Paragraph(escape(student.name),styles['Heading2']),Paragraph(escape(configured_text(current()['report_template'],'report_template')),styles['BodyText'])]
        for row in report_rows:
            body.append(Paragraph(escape(row['date']+' · '+row['session']),styles['Heading3']))
            for label,value in row['fields']: body.append(Paragraph(escape(label+': '+value),styles['BodyText']))
            body.append(Spacer(1,12))
        if request.GET.get('attendance'):
            body.append(Paragraph(_('Asistencia'),styles['Heading2']))
            for a in attendance: body.append(Paragraph(escape(str(timezone.localtime(a.session.start).date())+': '+a.get_status_display()),styles['BodyText']))
        doc.build(body); output.seek(0); return FileResponse(output,as_attachment=True,filename='informe-familia.pdf')
    return render(request,'core/reports.html',{'title':_('Informes'),'students':students(request.user),'groups':groups(request.user),'student':student,'report_rows':report_rows,'attendance':attendance if request.GET.get('attendance') else [],'sections':sections,'available_sections':allowed.items(),'domains':Resource.objects.values_list('domain',flat=True).distinct()})


@login_required
def group_report(request):
    require_module(request.user,'reports')
    selected=None; progress=Learning.objects.none(); attendance=Attendance.objects.none()
    if request.GET.get('group'):
        selected=get_object_or_404(groups(request.user),pk=request.GET['group'])
        progress=Learning.objects.filter(session__group=selected).select_related('student','session','author').order_by('-session__start','student__name')
        attendance=Attendance.objects.filter(session__group=selected).select_related('student','session').order_by('-session__start','student__name')
        for key,lookup in [('from','gte'),('to','lte')]:
            if request.GET.get(key):
                try: value=date.fromisoformat(request.GET[key])
                except ValueError: return HttpResponse(_('Fecha no válida.'),status=400)
                progress=progress.filter(**{'session__start__date__'+lookup:value}); attendance=attendance.filter(**{'session__start__date__'+lookup:value})
        if request.GET.get('domain'): progress=progress.filter(session__resource_snapshot__domain=request.GET['domain'])
    if request.GET.get('format')=='csv' and selected:
        audit(request.user,'report:group-export',selected)
        output=HttpResponse(content_type='text/csv; charset=utf-8');output['Content-Disposition']='attachment; filename="seguimiento-grupo.csv"'
        writer=csv.writer(output);writer.writerow([_('Alumno'),_('Fecha'),_('Sesión'),_('Reto'),_('Aprendizaje'),_('Evidencia'),_('Próximo paso')])
        def safe(value):
            value=str(value)
            return "'"+value if value.startswith(('=','+','-','@','\t','\r')) else value
        for r in progress: writer.writerow([safe(v) for v in [r.student.name,timezone.localtime(r.session.start).date(),r.session.title,r.challenge,_(r.get_learning_status_display()),r.evidence,r.next_step]])
        return output
    return render(request,'core/group_report.html',{'title':_('Seguimiento de grupo'),'groups':groups(request.user),'selected_group':selected,'progress':progress,'attendance_rows':attendance,'domains':Resource.objects.values_list('domain',flat=True).distinct()})

