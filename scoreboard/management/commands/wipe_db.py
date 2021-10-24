# Wipe everything in the database without changing the schema.
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from scoreboard.models import *

class Command(BaseCommand):
    help = 'Delete everything in the database'

    def handle(self, *args, **options):
        # This should definitely not get interleaved with other database
        # transactions. Use atomic.
        with transaction.atomic():
            Clan.objects.all().delete()
            Player.objects.all().delete()
            Game.objects.all().delete()
            Achievement.objects.all().delete()
            Conduct.objects.all().delete()
            Trophy.objects.all().delete()
            Source.objects.all().delete()
        print('Wiped all models.')
