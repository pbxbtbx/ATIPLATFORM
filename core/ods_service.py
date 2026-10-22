"""Plan de altas/matrículas y responsables ODS, validado de nuevo al confirmar."""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext as _
from .models import Student,Guardian,GuardianLink,Enrollment,ClassGroup
from .access import audit
from .services import move_student
from .ods_importing import key,contact_key


def build_plan(draft,form):
    options=form.cleaned_data
    rows=form.selected_rows(draft.payload)
    if not rows:raise ValidationError(_('Selecciona una pestaña y asigna al menos un grupo con filas incluidas.'))
    existing_students={}
    for obj in Student.objects.all():existing_students.setdefault(key(obj.name),[]).append(obj)
    existing_contacts={};existing_contact_names=set();seen_contact_names={}
    for obj in Guardian.objects.all():
        existing_contact_names.add(key(obj.name))
        existing_contacts.setdefault(contact_key({'name':obj.name,'phone':obj.phone,'email':obj.email}),[]).append(obj)
    pupils={};contacts={};enrollments=set();links={};items=[];counts={}
    for row in rows:
        # Los valores se actualizan dentro de la transacción, incluidos capacidad y vigencia.
        group=ClassGroup.objects.select_for_update().get(pk=options['group_'+row['group']].pk)
        if group.status!='active' or not group.starts<=options['joined']<=group.ends:raise ValidationError(_('El grupo debe estar activo y la matrícula dentro de sus fechas.'))
        student=options['student_'+row['id']]
        born=options['birth_'+row['id']]
        name=options['name_'+row['id']].strip()
        if not name:raise ValidationError(_('Indica el nombre completo de cada alumno incluido.'))
        name_key=key(name);pupil_key=('existing',str(student.pk)) if student else ('new',name_key)
        if student:
            student=Student.objects.select_for_update().get(pk=student.pk)
            if key(student.name)!=name_key or student.birth_date!=born:raise ValidationError(_('El alumno existente no coincide con el nombre y nacimiento revisados. No se sobrescribe su ficha.'))
        else:
            if existing_students.get(name_key):raise ValidationError(_('Ya existe un alumno con ese nombre. Selecciónalo expresamente en su fila o excluye la fila.'))
            student=Student(name=name,birth_date=born,joined=options['joined'])
            if born and born>options['joined']:raise ValidationError(_('El nacimiento no puede ser posterior a la incorporación.'))
            student.full_clean()
        if pupil_key in pupils:
            previous=pupils[pupil_key]
            if not options['merge_students'] or previous.birth_date!=born:raise ValidationError(_('Hay alumnos repetidos entre filas. Revisa y confirma la unión o excluye las filas repetidas.'))
            student=previous
        else:pupils[pupil_key]=student
        enrollment_key=(pupil_key,str(group.pk))
        already=not student._state.adding and Enrollment.objects.filter(student=student,group=group,ends=None).exists()
        if already:
            active=Enrollment.objects.get(student=student,group=group,ends=None)
            if options['joined']<active.starts:raise ValidationError(_('La matrícula existente comienza después de la fecha indicada. Revísala sin sobrescribir su historial.'))
        if enrollment_key not in enrollments and not already:
            counts[group.pk]=counts.get(group.pk,0)+1
            if Enrollment.objects.filter(group=group,ends=None).count()+counts[group.pk]>group.capacity:raise ValidationError(_('No hay plazas suficientes para todo el lote.'))
        enrollments.add(enrollment_key)
        row_contacts=[]
        for index,source in enumerate(row['contacts']):
            prefix=f"contact_{row['id']}_{index}_"
            if not options.get(prefix+'include'):continue
            raw={k:options[prefix+k].strip() for k in ('name','email','phone')}
            if not raw['name'].strip():raise ValidationError(_('Completa el nombre o desmarca este responsable. El alumno puede importarse sin este contacto.'))
            guardian=Guardian(**raw);guardian.full_clean()
            identity=contact_key(raw)
            separate=options.get(prefix+'distinct',False)
            share=options['reuse_contacts'] and bool(identity[1] or identity[2]) and not separate
            candidates=existing_contacts.get(identity,[])
            seen=seen_contact_names.setdefault(identity[0],set())
            ambiguous=(not candidates and identity[0] in existing_contact_names) or (seen and identity not in seen)
            if ambiguous and not separate:
                raise ValidationError({prefix+'distinct':_('El nombre coincide con otro responsable y los contactos difieren. Revisa los datos o confirma expresamente que es una persona diferente.')})
            if identity in seen and not share:
                raise ValidationError({prefix+'distinct':_('Hay responsables repetidos. Confirma su reutilización con contactos idénticos o revisa las filas.')})
            seen.add(identity)
            if candidates and not share:raise ValidationError(_('Ya existe un responsable con nombre y contactos idénticos. Confirma su reutilización o revisa la fila.'))
            if len(candidates)>1:raise ValidationError(_('Hay varios responsables idénticos en la plataforma. Revisa los duplicados antes de importar.'))
            gkey=('shared',identity) if share else ('row',row['id'],index)
            if share and gkey in contacts:guardian=contacts[gkey]
            elif share and candidates:guardian=candidates[0]
            contacts.setdefault(gkey,guardian)
            linkkey=(pupil_key,gkey)
            if linkkey not in links:
                existing_link=not student._state.adding and not guardian._state.adding and GuardianLink.objects.filter(student=student,guardian=guardian).exists()
                links[linkkey]={'student':student,'guardian':guardian,'existing':bool(existing_link),'legal':options['legal']}
            if not any(g.pk==guardian.pk for g in row_contacts):row_contacts.append(guardian)
        items.append({'row':row,'student':student,'group':group,'contacts':row_contacts,'existing':not student._state.adding,'already_enrolled':already})
    return {'legal':options['legal'],'items':items,'students':list(pupils.values()),'contacts':list({str(g.pk):g for g in contacts.values()}.values()),'links':list(links.values()),'joined':options['joined'],
            'excluded_contacts':sum(len(item['row']['contacts'])-len(item['contacts']) for item in items),'new_students':sum(s._state.adding for s in pupils.values()),'new_contacts':sum(g._state.adding for g in {str(g.pk):g for g in contacts.values()}.values()),'excluded':len(draft.payload['rows'])-len(rows)}


def commit_plan(plan,user):
    for student in plan['students']:
        if student._state.adding:student.save();audit(user,'import:create',student)
    for guardian in plan['contacts']:
        if guardian._state.adding:guardian.save();audit(user,'import:guardian',guardian)
    done=set()
    for item in plan['items']:
        student=item['student'];group=item['group'];pair=(student.pk,group.pk)
        if pair not in done and not item['already_enrolled']:
            move_student(student,group,plan['joined'],user)
        done.add(pair)
    for link in plan['links']:
        if not link['existing']:
            obj=GuardianLink.objects.create(student=link['student'],guardian=link['guardian'],relationship=_('Responsable comunicado'),legal=link['legal'])
            audit(user,'import:guardian_link',obj)


def plan_fingerprint(plan):
    import hashlib,json
    data={'legal':plan['legal'],'joined':str(plan['joined']),'items':[]}
    for item in plan['items']:
        student=item['student']
        data['items'].append({'row':item['row']['id'],'student':str(student.pk) if not student._state.adding else 'new',
            'name':student.name,'birth':str(student.birth_date),'group':str(item['group'].pk),'enrolled':item['already_enrolled'],
            'contacts':[{'id':str(g.pk) if not g._state.adding else 'new','name':g.name,'email':g.email,'phone':g.phone} for g in item['contacts']]})
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
