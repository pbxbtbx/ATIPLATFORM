"""Traduce etiquetas estándar al mostrarlas, no el contenido educativo guardado."""
from django.utils.translation import gettext
from .configuration import DEFAULT

def configured_text(value,key):
    return gettext(value) if value and value==DEFAULT.get(key) else value

def rubric_label(value):
    return gettext(str(value)) if value in DEFAULT['rubrics'] else value
