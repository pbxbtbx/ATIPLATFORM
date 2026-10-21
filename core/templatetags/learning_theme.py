from django import template
from core.presentation import RARITY_BY_STATUS
register = template.Library()

@register.filter
def learning_rarity(status):
    return RARITY_BY_STATUS.get(str(status), 'common')
