from django import template
from core.presentation import RARITY_BY_STATUS
register = template.Library()

@register.filter
def learning_rarity(status):
    return RARITY_BY_STATUS.get(str(status), 'common')


@register.filter
def learning_label(label):
    from django.utils.translation import gettext
    return gettext(str(label))

@register.filter
def configured_text(value,key):
    from core.i18n import configured_text as translate_configured
    return translate_configured(value,key)

@register.filter
def rubric_label(value):
    from core.i18n import rubric_label as translate_rubric
    return translate_rubric(value)
