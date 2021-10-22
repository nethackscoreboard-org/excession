from django.core.management.base import BaseCommand, CommandError
from scoreboard.models import Source, Game, Player, Clan
from scoreboard.parsers import XlogParser
from django.db import transaction
from django.db.models import Sum, Min, Max, Count, Q
from tnnt import uniqdeaths
import urllib

# Compute LeaderboardBaseFields data on all Players, and write it back.
def aggregatePlayerData():
    for plr in Player.objects.all():
        # all of the below only consider games done by this player
        gamesby_plr = Game.objects.filter(player=plr)
        # and a number of them only consider *ascended* games
        winsby_plr = gamesby_plr.filter(won=True)

        # simple aggregates (game counts)
        plr.total_games = gamesby_plr.count()
        plr.wins = winsby_plr.count()
        plr.games_over_1000_turns = gamesby_plr.filter(turns__gte=1000).count()
        # This is the source of truth for "what is a scummed game".
        plr.games_scummed = gamesby_plr.filter(
            Q(death='quit') | Q(death='escaped'),
            turns__lte=100).count()

        # a more complex aggregate
        # different from max_achieves_game; this is the total number of
        # distinct achievements across all games
        plr.unique_achievements = \
                gamesby_plr.aggregate(Count('achievements__id', distinct=True)) \
                ['achievements__id__count']

        # Unique deaths are more complex, but that's outsourced to another
        # module, so just get the set of unique deaths and take the length.
        plr.unique_deaths = len(uniqdeaths.compile_unique_deaths(gamesby_plr))

        # From here on, this is less about aggregating into one result, and more
        # about taking the game which is the player's best in some statistic.
        # Skip this if the player has no games, and for most of them, if the
        # player has no wins.
        if plr.total_games > 0:
            if plr.wins > 0:
                plr.min_score_asc = winsby_plr.order_by('points')[0]
                plr.max_score_asc = winsby_plr.order_by('-points')[0]
                plr.lowest_turncount_asc = winsby_plr.order_by('turns')[0]
                plr.fastest_realtime_asc = winsby_plr.order_by('wallclock')[0]
                plr.first_asc = winsby_plr.earliest('endtime')

            # These two are also Games which are the player's best in a
            # statistic, but require a bit more complex of a query.
            plr.max_achieves_game = \
                gamesby_plr.annotate(nachieve=Count('achievements__id', distinct=True)) \
                .order_by('-nachieve')[0]
            # TODO: Should this exclude some TNNT-added conducts?
            # For 2020 at least it didn't, so not a priority for 2021
            if plr.wins > 0:
                plr.max_conducts_asc = \
                    winsby_plr.annotate(ncond=Count('conducts__id', distinct=True)) \
                    .order_by('-ncond')[0]

        # TODO: longest_streak is NOT calculated yet!

        plr.save()

    # TODO: Trophies

# Compute LeaderboardBaseFields data on all Clans, and write it back.
# ASSUMPTION: It is run after aggregatePlayerData is run, and that each Player
# has had its leaderboard base fields updated.
def aggregateClanData():
    for clan in Clan.objects.all():
        # all of the below only consider games done by members of this clan
        # gamesby_clan = Game.objects.filter('player__clan'=clan)
        # # and a number of them only consider *ascended* games
        # winsby_clan = gamesby_clan.filter(won=True)
        clan_plrs = Player.objects.filter(clan=clan)

        # Basic aggregations can be computed pretty easily from the Players.
        # TODO: test: because of atomic, players have been save()d but not
        # actually committed to the database yet. Is this getting the right
        # info?
        aggrs_dict = clan_plrs.aggregate(Sum('total_games'),
                                         Sum('wins'),
                                         Sum('games_over_1000_turns'),
                                         Sum('games_scummed'),
                                         Max('longest_streak'))
        clan.total_games = aggrs_dict['total_games__sum']
        clan.wins = aggrs_dict['wins__sum']
        clan.games_over_1000_turns = aggrs_dict['games_over_1000_turns__sum']
        clan.games_scummed = aggrs_dict['games_scummed']
        clan.longest_streak = aggrs_dict['longest_streak__max']

        # Unfortunately, we have to do a rather nasty multiple join to get the
        # total number of distinct achievements earned collectively by all the
        # clan members. It's still better than getting and combining sets of all
        # the achievement titles, though.
        clan.unique_achievements = \
                clan_plrs.aggregate(Count('game__achievements__id', distinct=True)) \
                ['game__achievements__id__count']

        # Unique deaths for the clan requires constructing a QuerySet of all
        # games played by clan members.
        gamesby_clan = Game.objects.filter(player__clan=clan)
        clan.unique_deaths = len(uniqdeaths.compile_unique_deaths(gamesby_clan))

        # And then back to a (somewhat) simpler model, in which the clan can
        # just pick fields off its precomputed members.
        # As with players, skip this if the clan has no games.
        if clan.total_games > 0:
            # the pattern:
            # - join on the player's best Game in this stat
            # - order them by that stat
            # - pick the first Player from the resulting set
            # - set the clan leaderboard field to the corresponding Player field
            # This works nicely because even if all of the players in the clan
            # have a null instead of a Game for this field, it doesn't crash -
            # it instead just returns a None, which is correct - the clan has no
            # qualifying games for that stat.
            # The [0] reference should be fine - only way that would error is if
            # the clan had no members.
            # TODO: Should this instead be formatted without the minning and
            # maxing and instead just be e.g. for minscore
            # clan.min_score_asc = clan_plrs \
            #     .order_by('min_score_asc__points') \
            #     [0].min_score_asc
            # ... except for the #cond and #ach ones which do need to annotate with a Count
            clan.min_score_asc = clan_plrs \
                .annotate(minscore=Min('min_score_asc__points')) \
                .order_by('minscore') \
                [0].min_score_asc
            clan.max_score_asc = clan_plrs \
                .annotate(maxscore=Max('max_score_asc__points')) \
                .order_by('-maxscore') \
                [0].max_score_asc
            clan.lowest_turncount_asc = clan_plrs \
                .annotate(minturns=Min('lowest_turncount_asc__turns')) \
                .order_by('minturns') \
                [0].lowest_turncount_asc
            clan.fastest_realtime_asc = clan_plrs \
                .annotate(mintime=Min('fastest_realtime_asc__wallclock')) \
                .order_by('mintime') \
                [0].fastest_realtime_asc
            clan.first_asc = clan_plrs \
                .annotate(firsttime=Min('first_asc__endtime')) \
                .earliest('firsttime').first_asc
            clan.max_achieves_game = clan_plrs \
                .annotate(maxachieve=Count('max_achieves_game__achievements')) \
                .order_by('-maxachieve') \
                [0].max_achieves_game
            clan.max_conducts_asc = clan_plrs \
                .annotate(ncond=Count('max_conducts_asc__conducts')) \
                .order_by('-ncond') \
                [0].max_conducts_asc

        clan.save()

        # TODO: clan trophies

class Command(BaseCommand):
    help = 'Compute aggregate data from the set of all games'

    def handle(self, *args, **options):
        # This will end up doing a bunch of writes. Force them to happen all at
        # once with atomic().
        # If this is not done, someone could load a page when e.g. Player writes
        # have gone through but Clan writes have not, and wonder why the person
        # with the new best realtime game doesn't have their clan at the top of
        # the leaderboard. Or any of several similar problems.
        with transaction.atomic():
            aggregatePlayerData()
            aggregateClanData()
