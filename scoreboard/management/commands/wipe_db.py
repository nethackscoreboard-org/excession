# Wipe everything in the database without changing the schema.
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from scoreboard.models import *

class Command(BaseCommand):
    help = 'Delete everything in the database'

    # TODO: add options so that the default does not erase Clans or Players (but
    # does zero Players' fields)
    # something like:
    #   0 args: wipes Games, leaves Players and Clans intact.
    #   --full: wipes everything, including fixtures.
    #   --all-but-clans: wipes everything except Clan (which can't easily be
    #                    reconstructed).
    #   --non-fixtures: wipes Player, Clan, Game and leaves the fixtures intact.
    # Further TODO: print statements should reflect which models got wiped
    def handle(self, *args, **options):
        # This should definitely not get interleaved with other database
        # transactions. Use atomic.
        with transaction.atomic():
            Clan.objects.all().delete()
            Player.objects.all().delete()
            User.objects.all().delete()
            Game.objects.all().delete()
            Achievement.objects.all().delete()
            Conduct.objects.all().delete()
            Trophy.objects.all().delete()
            Source.objects.all().delete()
        print('Wiped all models.')
