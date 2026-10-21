"""Decoración del aprendizaje: no modifica estados, datos ni permisos."""
LEARNING_RARITIES = [
    {'key': 'common', 'name': 'Por aprender', 'color': 'Gris'},
    {'key': 'uncommon', 'name': 'En proceso', 'color': 'Verde'},
    {'key': 'rare', 'name': 'Con apoyo', 'color': 'Azul'},
    {'key': 'epic', 'name': 'Consolidado', 'color': 'Lila'},
    {'key': 'legendary', 'name': 'Legendario', 'color': 'Naranja'},
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
