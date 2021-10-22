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

    # First, get all unique, un-normalized deaths.
    raw_uniq_deaths = \
        gameQS.values_list('death', flat=True).distinct()
    # Then apply normalizations and rejections, and turn it into a set
    # to automatically remove any duplicates produced by normalization.
    return set(normalize(d) for d in raw_uniq_deaths if not reject(d))
