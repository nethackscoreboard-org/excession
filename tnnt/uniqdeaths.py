from tnnt.settings import UNIQUE_DEATH_REJECTIONS, UNIQUE_DEATH_NORMALIZATIONS
import re

def normalize(death):
    # Given a death string, apply normalizations from settings.
    for regtuple in UNIQUE_DEATH_NORMALIZATIONS:
        death = re.sub(regtuple[0], regtuple[1], death)
    return death

def reject(death):
    # Given a death string, return True if it should be excluded as a
    # unique death and False if not.
    for regex in UNIQUE_DEATH_REJECTIONS:
        if re.search(regex, death) is not None:
            return True
    return False

def compile_unique_deaths(gameQS):
    # Given a QuerySet of Game objects, return a set containing strings of all
    # the unique deaths from those games after rejections and normalizations are
    # applied.
    # This is primarily for aggregation, and runs somewhat faster than it would
    # if we wanted to return the players who got a death and when. This is a
    # post 2021 TODO.

    # First, get all unique, un-normalized deaths.
    raw_uniq_deaths = \
        gameQS.values_list('death', flat=True).distinct()
    # Then apply normalizations and rejections, and turn it into a set
    # to automatically remove any duplicates produced by normalization.
    return set(normalize(d) for d in raw_uniq_deaths if not reject(d))

# post 2021 TODO: showing unique deaths of a player or clan:
# 1. list(Game.objects.values_list('death', 'player__name', 'endtime'))
# 2. iterate through list, filtering any death for which reject is True, and
#    normalizing all death strings.
# 3. sort by first death, then endtime.
# 4. filter again by taking only the first player/endtime for each death and
#    ignoring later ones.
