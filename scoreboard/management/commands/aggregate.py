from django.core.management.base import BaseCommand, CommandError
from scoreboard.models import Source, Game, Player
from scoreboard.parsers import XlogParser
import urllib


def update_leaderboard_fields(entity, game):
    if entity.max_achieves_game is None or game.achievements.count() > entity.max_achieves_game.achievements.count():
        entity.max_achieves_game = game

    if not game.won:
        entity.save()
        return

    if entity.lowest_turncount_asc is None or game.turns < entity.lowest_turncount_asc.turns:
        entity.lowest_turncount_asc = game

    if entity.fastest_realtime_asc is None or game.realtime < entity.fastest_realtime_asc.realtime:
        entity.fastest_realtime_asc = game

    if entity.max_conducts_asc is None or game.conducts.count() > entity.max_conducts_asc.conducts.count():
        entity.max_conducts_asc = game

    if entity.min_score_asc is None or game.points < entity.min_score_asc.points:
        entity.min_score_asc = game

    if entity.max_score_asc is None or game.points > entity.max_score_asc.points:
        entity.max_score_asc = game

    if entity.first_asc is None or game.endtime < entity.first_asc.endtime:
        entity.first_asc = game

    entity.save()

class Command(BaseCommand):
    help = 'Compute aggregate data from the set of all games'

    def handle(self, *args, **options):
        for game in Game.objects.all():
            update_leaderboard_fields(game.player, game)
            if game.player.clan is not None:
                update_leaderboard_fields(game.player.clan, game)
