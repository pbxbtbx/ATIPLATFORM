from django import forms
from django.utils.translation import gettext_lazy as _
from .access import groups
from .models import ClassGroup


class UploadImportForm(forms.Form):
    kind=forms.ChoiceField(label=_('Qué quieres añadir'),choices=[('students',_('Alumnado · CSV o lista')),('sessions',_('Sesiones · CSV')),('word',_('Ficha de sesión · Word DOCX'))])
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
    group=forms.ModelChoiceField(label=_('Grupo de destino'),queryset=ClassGroup.objects.none())
    joined=forms.DateField(label=_('Fecha de incorporación'),required=False,widget=forms.DateInput(attrs={'type':'date'}))
    teacher=forms.ModelChoiceField(label=_('Docente'),queryset=None,required=False)
    title=forms.CharField(label=_('Título'),max_length=200,required=False)
    number=forms.IntegerField(label=_('Número de sesión'),min_value=1,required=False)
    start=forms.DateTimeField(label=_('Inicio · Europe/Madrid'),required=False,widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    duration=forms.IntegerField(label=_('Duración en minutos'),min_value=1,max_value=720,required=False)
    goals=forms.CharField(label=_('Objetivos'),widget=forms.Textarea,required=False,max_length=100000)
    materials=forms.CharField(label=_('Materiales y preparación'),widget=forms.Textarea,required=False,max_length=100000)
    planned=forms.CharField(label=_('Actividades previstas y apoyos'),widget=forms.Textarea,required=False,max_length=150000)
    def __init__(self,*args,user,kind,**kwargs):
        super().__init__(*args,**kwargs)
        from django.contrib.auth.models import User
        self.fields['group'].queryset=groups(user).filter(status='active')
        self.fields['teacher'].queryset=User.objects.filter(is_active=True,classgroup__in=groups(user)).distinct()
        keep=['group','joined'] if kind=='students' else ['group','teacher'] if kind=='sessions' else ['group','teacher','title','number','start','duration','goals','materials','planned']
        for field in list(self.fields):
            if field not in keep: del self.fields[field]
        for name in keep:
            if name not in ('goals','materials','planned'): self.fields[name].required=True
