from django.utils.translation import gettext_lazy as _
"""Decoración del aprendizaje: no modifica estados, datos ni permisos."""
LEARNING_RARITIES = [
    {'key': 'common', 'name': _('Por aprender'), 'color': _('Gris')},
    {'key': 'uncommon', 'name': _('En proceso'), 'color': _('Verde')},
    {'key': 'rare', 'name': _('Con apoyo'), 'color': _('Azul')},
    {'key': 'epic', 'name': _('Consolidado'), 'color': _('Lila')},
    {'key': 'legendary', 'name': _('Legendario'), 'color': _('Naranja')},
]
RARITY_BY_STATUS = {
    'new': 'common',
    'progress': 'uncommon',
    'supported': 'rare',
    'consolidated': 'epic',
    'autonomous': 'legendary',
    # Retomar es una situación de trabajo, no un nivel superior de adquisición.
    'resume': 'paused',
}
