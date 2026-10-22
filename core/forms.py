from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import *

class VersionedForm(forms.ModelForm):
    expected_version = forms.IntegerField(widget=forms.HiddenInput,required=False)
    def clean(self):
        data=super().clean()
        for start,end in [('starts','ends'),('start','end')]:
            if data.get(start) and data.get(end) and data[end]<data[start]: self.add_error(end,_('La fecha final no puede preceder a la inicial.'))
        return data
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance.pk: self.fields['expected_version'].initial=self.instance.version
        from .configuration import current
        labels=current()['labels']
        for name,field in self.fields.items():
            prefix=self._meta.model._meta.model_name+'.'+name
            field.label=labels.get(prefix+'.label',field.label)
            field.help_text=labels.get(prefix+'.help',field.help_text)
            if isinstance(field,forms.DateTimeField):
                field.widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M',attrs={'type':'datetime-local'})
                field.input_formats=['%Y-%m-%dT%H:%M']
            elif isinstance(field,forms.DateField): field.widget=forms.DateInput(format='%Y-%m-%d',attrs={'type':'date'})
            elif isinstance(field.widget,forms.Textarea): field.widget.attrs['rows']=3

def form_for(model,fields):
    class Generated(VersionedForm):
        class Meta:
            pass
    Generated.Meta.model=model
    Generated.Meta.fields=fields
    return forms.modelform_factory(model,form=Generated,fields=fields)

YearForm=form_for(AcademicYear,['name','starts','ends','archived'])
GroupForm=form_for(ClassGroup,['name','kind','year','location','teachers','schedule','starts','ends','capacity','plan','status'])
StudentForm=form_for(Student,['name','preferred_name','birth_date','joined','status','contact','interests','experience','strengths','preferences','strategies'])
GuardianForm=form_for(Guardian,['name','phone','email'])
LinkForm=form_for(GuardianLink,['guardian','relationship','priority','legal','emergency','pickup','notes'])
ResourceForm=form_for(Resource,['title','kind','domain','description','goals','prerequisites','duration','materials','instructions','challenges','supports','criteria'])
SessionForm=form_for(Session,['group','teacher','title','number','start','end','resource','goals','materials','planned','actual','pending','adaptations','notes','next_steps','status'])
LearningForm=form_for(Learning,['challenge','objective','evidence','achievement','difficulty','support','student_comment','next_step','internal_notes','activity_status','learning_status'])
RestrictedForm=form_for(RestrictedNote,['kind','content','source','relevance','support','review'])
ConsentForm=form_for(Consent,['purpose','text_version','granted_at','withdrawn_at','image_use'])
EvidenceForm=form_for(Evidence,['session','title','file','url','visibility'])
TaskForm=form_for(Task,['title','due','done'])
HolidayForm=form_for(Holiday,['title','start','end'])
SequenceForm=form_for(Sequence,['name','resources','group'])

class UserForm(forms.Form):
    username=forms.CharField(label=_('Usuario'),max_length=150)
    first_name=forms.CharField(label=_('Nombre'),max_length=100)
    password=forms.CharField(label=_('Contraseña inicial'),widget=forms.PasswordInput)
    role=forms.ChoiceField(label=_('Rol'),choices=Profile.ROLES)
    sensitive_access=forms.BooleanField(label=_('Permiso específico de información restringida'),required=False)
    development_access=forms.BooleanField(label=_('Permiso específico de desarrollo'),required=False)
    def clean_password(self):
        value=self.cleaned_data['password']; validate_password(value); return value
    def clean_username(self):
        value=self.cleaned_data['username']
        if User.objects.filter(username=value).exists(): raise forms.ValidationError(_('Usuario ya existente.'))
        return value

class DynamicStudentForm(StudentForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        from .configuration import current
        self.definitions=current()['custom_fields']
        for field in self.definitions:
            opts={'label':field['label'],'required':field['required'],'initial':self.instance.custom_values.get(field['key'],'')}
            if field['type']=='choice': self.fields['custom_'+field['key']]=forms.ChoiceField(choices=[('','—')]+[(v,v) for v in field['options']],**opts)
            else: self.fields['custom_'+field['key']]=forms.CharField(max_length=500,**opts)
    def save(self,commit=True):
        obj=super().save(commit=False)
        # Hidden/retired definitions retain their stored values.
        obj.custom_values={**obj.custom_values,**{f['key']:self.cleaned_data['custom_'+f['key']] for f in self.definitions}}
        if commit: obj.save(); self.save_m2m()
        return obj

class EditUserForm(forms.Form):
    first_name=forms.CharField(label=_('Nombre'),max_length=100)
    role=forms.ChoiceField(label=_('Rol'),choices=Profile.ROLES)
    active=forms.BooleanField(label=_('Cuenta activa'),required=False)
    sensitive_access=forms.BooleanField(label=_('Permiso específico de información restringida'),required=False)
    development_access=forms.BooleanField(label=_('Permiso específico de desarrollo'),required=False)


class AppearanceForm(forms.Form):
    learning_palette=forms.ChoiceField(label=_("Colores del aprendizaje"),choices=Profile._meta.get_field("learning_palette").choices,required=False)
    theme=forms.ChoiceField(label=_('Elige tu estilo'),choices=Profile._meta.get_field('theme').choices,widget=forms.RadioSelect)
