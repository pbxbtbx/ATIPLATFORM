"""Scoped list filters; no access to contacts, restricted notes or global options."""
import unicodedata
from django import forms
from django.utils.translation import gettext_lazy as _
from core.models import AcademicYear, ClassGroup, Student


def search_key(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def text_search(queryset, query, *fields):
    """Unicode/diacritic matching for the pilot's small lists, AFTER permission filters."""
    tokens = search_key(query).split()
    if not tokens:
        return queryset
    matches = []
    for row in queryset.values_list('pk', *fields):
        haystack = search_key(' '.join(value or '' for value in row[1:]))
        if all(token in haystack for token in tokens):
            matches.append(row[0])
    return queryset.filter(pk__in=matches)


class StudentListFilters(forms.Form):
    q = forms.CharField(label=_('Buscar alumno por nombre o apellidos'), max_length=150, required=False,
                        widget=forms.TextInput(attrs={'type': 'search', 'placeholder': _('Escribe un nombre, apellidos o nombre preferido'), 'autocomplete': 'off'}))
    group = forms.ChoiceField(label=_('Grupo con matrícula abierta'), required=False)
    status = forms.ChoiceField(label=_('Estado del alumno'), required=False,
                              choices=[('', _('Todos los estados')), *Student._meta.get_field('status').choices])
    def __init__(self, *args, allowed_groups, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].choices = [('', _('Todos los grupos')), *[(str(g.pk), g.name) for g in allowed_groups.order_by('name', 'pk')]]


class GroupListFilters(forms.Form):
    q = forms.CharField(label=_('Buscar grupos'), max_length=150, required=False,
                        widget=forms.TextInput(attrs={'type': 'search', 'placeholder': _('Nombre, ubicación u horario'), 'autocomplete': 'off'}))
    kind = forms.ChoiceField(label=_('Tipo de clase'), required=False, choices=[('', _('Todos los tipos')), *ClassGroup.TYPES])
    year = forms.ChoiceField(label=_('Curso académico'), required=False)
    location = forms.ChoiceField(label=_('Ubicación'), required=False)
    status = forms.ChoiceField(label=_('Estado del grupo'), required=False,
                              choices=[('', _('Todos los estados')), *ClassGroup._meta.get_field('status').choices])
    order = forms.ChoiceField(label=_('Ordenar por'), required=False, choices=[('name', _('Nombre')), ('location', _('Ubicación')), ('kind', _('Tipo de clase')), ('starts', _('Fecha de inicio'))])
    def __init__(self, *args, allowed_groups, **kwargs):
        super().__init__(*args, **kwargs)
        years = AcademicYear.objects.filter(classgroup__in=allowed_groups).distinct().order_by('-starts', 'name', 'pk')
        self.fields['year'].choices = [('', _('Todos los cursos')), *[(str(y.pk), y.name) for y in years]]
        self.fields['location'].choices = [('', _('Todas las ubicaciones')), *[(v, v) for v in allowed_groups.exclude(location='').order_by('location').values_list('location', flat=True).distinct()]]
        self.fields['order'].initial = 'name'
