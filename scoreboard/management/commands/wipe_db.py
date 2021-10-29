# Wipe everything in the database without changing the schema.
from django.core.management.base import BaseCommand
from django.db import transaction
from scoreboard.models import *


@transaction.atomic
def wipe_leaderboard_fields(entity):
    entity.longest_streak = 0
    entity.unique_deaths = 0
    entity.unique_ascs = 0
    entity.unique_achievements = 0
    entity.games_over_1000_turns = 0
    entity.games_scummed = 0
    entity.total_games = 0
    entity.wins = 0
    entity.trophies.clear()
    entity.save()


@transaction.atomic
def clear_player_and_clan_fields():
    for player in Player.objects.all():
        wipe_leaderboard_fields(player)
    for clan in Clan.objects.all():
        wipe_leaderboard_fields(clan)


@transaction.atomic
def wipe_games():
    Game.objects.all().delete()
    clear_player_and_clan_fields()


@transaction.atomic
def wipe_all_but_clans():
    Clan.objects.all().delete()
    Player.objects.all().delete()
    User.objects.all().delete()
    clear_player_and_clan_fields()


@transaction.atomic
def wipe_non_fixtures():
    Clan.objects.all().delete()
    Player.objects.all().delete()
    User.objects.all().delete()
    Game.objects.all().delete()


@transaction.atomic
def wipe_all():
    Clan.objects.all().delete()
    Player.objects.all().delete()
    User.objects.all().delete()
    Game.objects.all().delete()
    Achievement.objects.all().delete()
    Conduct.objects.all().delete()
    Trophy.objects.all().delete()
    Source.objects.all().delete()


class Command(BaseCommand):
    help = 'Delete models in the database, with no args fixtures and player-clan relationships remain intact.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all objects from all models. Warning: this supersedes other flags.',
        )
        parser.add_argument(
            '--all-but-clans',
            action='store_true',
            help='Delete all objects from all models, but keep Player and Clan relationships intact.',
        )
        parser.add_argument(
            '--non-fixtures',
            action='store_true',
            help='Delete all objects from all models, except those that come from static fixtures.',
        )

    def handle(self, *args, **options):
        # Further TODO: print statements should reflect which models got wiped
        if options['all']:
            wipe_all()
        elif options['all-but-clans']:
            wipe_all_but_clans()
        elif options['non-fixtures']:
            wipe_non_fixtures()
        else:
            wipe_games()
