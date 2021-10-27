from django import template
from django.forms.models import model_to_dict
from scoreboard.models import Game

register = template.Library()

# https://stackoverflow.com/questions/8000022/django-template-how-to-look-up-a-dictionary-value-with-a-variable#
# https://code.djangoproject.com/ticket/3371 >:(
@register.filter
def get_model_field(model_instance, key):
    # Get a raw field from a model. This is not suitable for foreign key fields
    # because it will just return the id.
    # subscript will cause a KeyError if the key is not found, which is what we
    # want - the keys in this case are provided only by templates, not user input

    # TODO: Ugly, and extra db accesses. But workable for the time being.
    # Revisit if optimization is needed.
    if key == 'maxcond':
        return model_instance.conducts.count()
    if key == 'mostach':
        return model_instance.achievements.count()
    return model_to_dict(model_instance)[key]

@register.filter
def get_dict_field(dictionary, key):
    # Get a field from a dictionary.
    return dictionary[key]

@register.filter
def get_game_field(player_or_clan, key):
    # Get a Game object from a player or clan field (field must be a ForeignKey
    # to Game).
    return Game.objects.get(id=get_model_field(player_or_clan, key))
