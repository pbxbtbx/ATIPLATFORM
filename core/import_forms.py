from django import forms
from django.utils.translation import gettext_lazy as _
from .access import groups
from .models import ClassGroup
from .curriculum import AREA_CHOICES


class UploadImportForm(forms.Form):
    kind=forms.ChoiceField(label=_('Qué quieres añadir'),choices=[('ods',_('Alumnado, responsables y grupos · ODS')),('students',_('Alumnado · CSV o lista')),('sessions',_('Sesiones · CSV')),('word',_('Ficha de sesión · Word DOCX'))])
    file=forms.FileField(label=_('Archivo (máximo 2 MB)'),required=False)
    names=forms.CharField(label=_('Alta de varios alumnos: un nombre completo por línea'),widget=forms.Textarea(attrs={'rows':6}),required=False,max_length=40000)
    def clean(self):
        data=super().clean()
        if bool(data.get('file')) == bool(data.get('names')):
            raise forms.ValidationError(_('Selecciona un archivo o escribe una lista, pero no ambos.'))
        if data.get('names') and data.get('kind')!='students':
            raise forms.ValidationError(_('La lista de nombres solo permite añadir alumnado.'))
        return data


class ImportOptionsForm(forms.Form):
    content_area=forms.ChoiceField(label=_('Bloque de contenidos'),choices=AREA_CHOICES,required=False)
    group=forms.ModelChoiceField(label=_('Grupo de destino'),queryset=ClassGroup.objects.none())
    joined=forms.DateField(label=_('Fecha de incorporación'),required=False,widget=forms.DateInput(attrs={'type':'date'}))
    teacher=forms.ModelChoiceField(label=_('Docente'),queryset=None,required=False)
    title=forms.CharField(label=_('Título'),max_length=200,required=False)
    number=forms.IntegerField(label=_('Número de sesión'),min_value=1,required=False)
    start=forms.DateTimeField(label=_('Inicio · Europe/Madrid'),required=False,widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    duration=forms.IntegerField(label=_('Duración en minutos'),min_value=1,max_value=720,required=False)
    goals=forms.CharField(label=_('Objetivos'),widget=forms.Textarea,required=False,max_length=100000)
    materials=forms.CharField(label=_('Materiales y preparación'),widget=forms.Textarea,required=False,max_length=100000)
    diversity=forms.CharField(label=_('Atención a la diversidad · apoyos previstos'),widget=forms.Textarea,required=False,max_length=100000)
    planned=forms.CharField(label=_('Actividades previstas y apoyos'),widget=forms.Textarea,required=False,max_length=150000)
    def __init__(self,*args,user,kind,**kwargs):
        super().__init__(*args,**kwargs)
        from django.contrib.auth.models import User
        self.fields['group'].queryset=groups(user).filter(status='active')
        self.fields['teacher'].queryset=User.objects.filter(is_active=True,classgroup__in=groups(user)).distinct()
        keep=['group','joined'] if kind=='students' else ['group','teacher','content_area'] if kind=='sessions' else ['group','teacher','content_area','title','number','start','duration','goals','materials','diversity','planned']
        for field in list(self.fields):
            if field not in keep: del self.fields[field]
        for name in keep:
            if name not in ('content_area','goals','materials','diversity','planned'): self.fields[name].required=True


class ODSImportForm(forms.Form):
    sheets=forms.MultipleChoiceField(label=_('Pestañas que quieres importar'),choices=[],widget=forms.CheckboxSelectMultiple)
    joined=forms.DateField(label=_('Fecha de incorporación y matrícula'),widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'}))
    merge_students=forms.BooleanField(label=_('Unir filas con el mismo nombre completo y nacimiento tras revisarlas'),required=False)
    reuse_contacts=forms.BooleanField(label=_('Reutilizar responsables con nombre y contactos idénticos tras revisarlos'),required=False)
    legal=forms.BooleanField(label=_('He verificado la tutela legal para los vínculos nuevos'),required=False)
    rows=forms.MultipleChoiceField(label=_('Filas incluidas'),choices=[],required=False)
    def __init__(self,*args,payload,**kwargs):
        super().__init__(*args,**kwargs)
        self.payload=payload
        from .models import Student
        from .ods_importing import key
        self.fields['sheets'].choices=[(s['id'],f"{s['name']} · {s['rows']}") for s in payload['sheets'] if s['rows']]
        self.fields['rows'].choices=[(r['id'],r['id']) for r in payload['rows']]
        self.fields['rows'].initial=[r['id'] for r in payload['rows']]
        sheet_names={s['id']:s['name'] for s in payload['sheets']}
        for n,group in enumerate(payload['groups']):
            self.fields['group_'+str(n)]=forms.ModelChoiceField(label=f"{sheet_names[group['sheet']]} · {group['label'] or _('Sin grupo indicado')}",queryset=ClassGroup.objects.filter(status='active'),required=False,empty_label=_('No importar este grupo'))
        candidates={}
        for pk,name in Student.objects.values_list('pk','name'):candidates.setdefault(key(name),[]).append(pk)
        for row in payload['rows']:
            rid=row['id']
            self.fields['name_'+rid]=forms.CharField(label=_('Nombre completo revisado'),max_length=200,required=False,initial=row['name'])
            self.fields['birth_'+rid]=forms.DateField(label=_('Nacimiento (opcional)'),required=False,initial=row['birth'],input_formats=['%Y-%m-%d'],widget=forms.TextInput(attrs={'placeholder':'AAAA-MM-DD','inputmode':'numeric'}))
            self.fields['student_'+rid]=forms.ModelChoiceField(label=_('Vincular alumno existente'),queryset=Student.objects.filter(pk__in=candidates.get(key(row['name']),[])),required=False,empty_label=_('Crear alumno nuevo'))
            for n,contact in enumerate(row['contacts']):
                prefix=f'contact_{rid}_{n}_'
                self.fields[prefix+'distinct']=forms.BooleanField(label=_('Es una persona diferente aunque coincida su nombre; lo he comprobado'),required=False)
                self.fields[prefix+'include']=forms.BooleanField(label=_('Incluir responsable'),required=False,initial=bool(contact['name'].strip()))
                self.fields[prefix+'name']=forms.CharField(label=_('Nombre del responsable'),required=False,max_length=200,initial=contact['name'])
                self.fields[prefix+'email']=forms.EmailField(label=_('Correo del responsable'),required=False,initial=contact['email'])
                self.fields[prefix+'phone']=forms.CharField(label=_('Teléfono del responsable'),required=False,max_length=60,initial=contact['phone'])
    def selected_rows(self,payload):
        selected=set(self.cleaned_data['rows']);sheets=set(self.cleaned_data['sheets'])
        return [r for r in payload['rows'] if r['id'] in selected and r['sheet'] in sheets and self.cleaned_data.get('group_'+r['group'])]

    def full_clean(self):
        # No validar ni importar campos de hojas, grupos o filas excluidos.
        original=self.fields
        if self.is_bound:
            rows=set(self.data.getlist('rows'));sheets=set(self.data.getlist('sheets'))
            active={r['id'] for r in self.payload['rows'] if r['id'] in rows and r['sheet'] in sheets and self.data.get('group_'+r['group'])}
            filtered={}
            for name,field in original.items():
                if name.startswith(('name_','birth_','student_')) and name.split('_')[1] not in active:continue
                if name.startswith('contact_'):
                    parts=name.split('_')
                    if parts[1] not in active:continue
                    if parts[-1]!='include' and not forms.BooleanField(required=False).clean(self.data.get('_'.join(parts[:-1])+'_include')):continue
                filtered[name]=field
            self.fields=filtered
        try:super().full_clean()
        finally:self.fields=original

    def clean(self):
        data=super().clean()
        if 'rows' not in data or 'sheets' not in data:return data
        for row in self.selected_rows(self.payload):
            rid=row['id']
            if not data.get('name_'+rid):self.add_error('name_'+rid,_('Indica el nombre completo de cada alumno incluido.'))
            for n,source in enumerate(row['contacts']):
                prefix=f'contact_{rid}_{n}_'
                if data.get(prefix+'include') and not data.get(prefix+'name'):
                    self.add_error(prefix+'name',_('Completa el nombre o desmarca este responsable. El alumno puede importarse sin este contacto.'))
        return data
