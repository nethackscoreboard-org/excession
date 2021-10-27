from django.core.management.base import BaseCommand
from scoreboard.models import Source, Game, Player, Clan, Trophy, Achievement, Conduct
from scoreboard.parsers import XlogParser
from django.db import transaction
from django.db.models import Sum, Min, Max, Count
from tnnt import uniqdeaths
import urllib
import logging

logger = logging.getLogger() # root logger

# Optimizations: these don't change over the lifetime of the tournament. Run
# these queries once when this module is loaded so that they don't have to be
# hit multiple times in loops.
TOTAL_ACHIEVEMENTS = Achievement.objects.count()
TOTAL_CONDUCTS = Conduct.objects.count()
TROPHIES = { tr.name: tr for tr in Trophy.objects.all() }

# These are determined by NetHack and there's no expectation that TNNT would
# ever change them. However, they may need to change if changes are made to
# vanilla NetHack which are then incorporated into TNNT (for instance, if the
# DevTeam adds a new role).
TOTAL_GENDERS = 2
TOTAL_ALIGNMENTS = 3
TOTAL_RACES = 5
TOTAL_ROLES = 13
TOTAL_POSSIBLE_COMBOS = 73
great_lesser_race = {
    'Dwarf': { 'race': 'Dwa', 'req_roles': set(['Arc','Cav','Val']) },
    'Orc'  : { 'race': 'Orc', 'req_roles': set(['Bar','Ran','Rog','Wiz']) },
    'Elf'  : { 'race': 'Elf', 'req_roles': set(['Pri','Ran','Wiz']) },
    'Gnome': { 'race': 'Gno', 'req_roles': set(['Arc','Cav','Hea','Ran','Wiz']) },
    'Human': { 'race': 'Hum', 'req_roles': set(['Kni','Mon','Sam','Tou']) }
}
great_lesser_role = {
    'Archeologist': {
        'role': 'Arc',
        'req_race_algn': set(['Dwa-Law','Hum-Law','Hum-Neu','Gno-Neu'])
    },
    'Barbarian': {
        'role': 'Bar',
        'req_race_algn': set(['Hum-Neu','Hum-Cha','Orc-Cha'])
    },
    'Caveperson': {
        'role': 'Cav',
        'req_race_algn': set(['Dwa-Law','Hum-Law','Hum-Neu','Gno-Neu'])
    },
    'Healer': {
        'role': 'Hea',
        'req_race_algn': set(['Hum-Neu','Gno-Neu'])
    },
    'Monk': {
        'role': 'Mon',
        'req_race_algn': set(['Hum-Law','Hum-Neu','Hum-Cha'])
    },
    'Priest': {
        'role': 'Pri',
        'req_race_algn': set(['Hum-Law','Hum-Neu','Hum-Cha','Elf-Cha'])
    },
    'Ranger': {
        'role': 'Ran',
        'req_race_algn': set(['Hum-Neu','Gno-Neu','Hum-Cha','Elf-Cha','Orc-Cha'])
    },
    'Rogue': {
        'role': 'Rog',
        'req_race_algn': set(['Hum-Cha','Orc-Cha'])
    },
    'Valkyrie': {
        'role': 'Val',
        'req_race_algn': set(['Dwa-Law','Hum-Law','Hum-Neu'])
    },
    'Wizard': {
        'role': 'Wiz',
        'req_race_algn': set(['Hum-Neu','Gno-Neu','Hum-Cha','Elf-Cha','Orc-Cha'])
    },
}

# Determine and award trophies to a player or clan.
# ASSUMPTION: The player's LeaderboardBaseFields are already computed.
# allgames_qs is a QuerySet of all Games by this player/clan. For most
# operations, we convert this to a list to avoid thrashing the database too
# much, while keeping the queryset around for the few things that need it. (I'm
# not totally sure if this would actually do that with repeated queries, but I
# suspect it would.)
# IMPORTANT: Nothing in here should use gender or align! gender0 and align0 only!
def awardTrophies(player_or_clan, allgames_qs):
    # First, a small optimization: exclude all games that are neither ascensions
    # nor have mines/soko complete. These won't contribute to any trophies.
    # (Never Scum a Game is based off the precomputed games_scummed.)
    allgames = [ g for g in allgames_qs.all() if g.won or g.mines_soko ]

    # It might be possible to optimize some of this by doing a big, single pass
    # through allgames and storing various bits of data in sets, but there
    # currently isn't a demonstrated need for this.

    # Great Race
    for fullrace, details in great_lesser_race.items():
        # Compute all distinct roles for which there exists a winning game
        # that has this race. If it matches the trophy required set, award it.
        if details['req_roles'] == set(g.role for g in allgames
                                       if g.won and g.race == details['race']):
            player_or_clan.trophies.add(TROPHIES['Great %s' % fullrace])

        # Then the same for mines_soko games.
        if details['req_roles'] == set(g.role for g in allgames
                                       if g.mines_soko and g.race == details['race']):
            player_or_clan.trophies.add(TROPHIES['Lesser %s' % fullrace])

    # Great Role
    for fullrole, details in great_lesser_role.items():
        # Similar to above. Compute distinct race-align combos.
        if details['req_race_algn'] == set('%s-%s' % (g.race, g.align0) for g in allgames
                                           if g.won and g.role == details['role']):
            player_or_clan.trophies.add(TROPHIES['Great %s' % fullrole])

        # And the same for mines_soko.
        if details['req_race_algn'] == set('%s-%s' % (g.race, g.align0) for g in allgames
                                           if g.mines_soko and g.role == details['role']):
            player_or_clan.trophies.add(TROPHIES['Lesser %s' % fullrole])

    # All Foo
    if len(set(g.gender0 for g in allgames if g.won)) == TOTAL_GENDERS:
        player_or_clan.trophies.add(TROPHIES['Both Genders'])
    if len(set(g.align0 for g in allgames if g.won)) == TOTAL_ALIGNMENTS:
        player_or_clan.trophies.add(TROPHIES['All Alignments'])
    if len(set(g.race for g in allgames if g.won)) == TOTAL_RACES:
        player_or_clan.trophies.add(TROPHIES['All Races'])
    if len(set(g.role for g in allgames if g.won)) == TOTAL_ROLES:
        player_or_clan.trophies.add(TROPHIES['All Roles'])
    if player_or_clan.unique_achievements == TOTAL_ACHIEVEMENTS:
        player_or_clan.trophies.add(TROPHIES['All Achievements'])
    # All Conducts kind of has to be a query, since we don't track "number of
    # discrete conducts across all games" on a leaderboard.
    unique_conducts = allgames_qs.filter(won=True) \
        .aggregate(Count('conducts__id', distinct=True)) \
        ['conducts__id__count']
    if unique_conducts == TOTAL_CONDUCTS:
        player_or_clan.trophies.add(TROPHIES['All Conducts'])
    if player_or_clan.unique_ascs == TOTAL_POSSIBLE_COMBOS:
        player_or_clan.trophies.add(TROPHIES['NetHack Master'])
        if unique_conducts == TOTAL_CONDUCTS:
            player_or_clan.trophies.add(TROPHIES['NetHack Dominator'])

    # Never Scum a Game is a weird trophy in that a player has it by default,
    # and can lose it at a later point.
    try:
        nsag = player_or_clan.trophies.get(name='Never Scum a Game')
        if player_or_clan.games_scummed > 0:
            player_or_clan.trophies.remove(nsag)
    except Trophy.DoesNotExist:
        if player_or_clan.total_games > 0 and player_or_clan.games_scummed == 0:
            player_or_clan.trophies.add(TROPHIES['Never Scum a Game'])

    # Never Kill Foo
    for g in allgames_qs.filter(won=True).prefetch_related('conducts'):
        for c in g.conducts.all():
            if c.shortname == 'neme':
                player_or_clan.trophies.add(TROPHIES['Never Kill the Quest Nemesis'])
            elif c.shortname == 'vlad':
                player_or_clan.trophies.add(TROPHIES['Never Kill Vlad'])
            elif c.shortname == 'wiz':
                player_or_clan.trophies.add(TROPHIES['Never Kill Rodney'])
            elif c.shortname == 'prst':
                player_or_clan.trophies.add(TROPHIES['Never Kill the High Priest of Moloch'])
            elif c.shortname == 'ride':
                player_or_clan.trophies.add(TROPHIES['Never Kill a Rider'])


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
            death__in=('quit','escaped'),
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

        # Unique ascs are a one-liner.
        plr.unique_ascs = len(set(g.rrga() for g in winsby_plr))

        # Streaks are computed on their own as well.
        streak_lengths = list(map(lambda s: len(s.games), plr.get_streaks()))
        if len(streak_lengths) == 0:
            plr.longest_streak = 0
        else:
            plr.longest_streak = max(streak_lengths)

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

        plr.save()
        awardTrophies(plr, gamesby_plr)
    logging.info('aggregatePlayerData complete')

# Compute LeaderboardBaseFields data on all Clans, and write it back.
# ASSUMPTION: It is run after aggregatePlayerData is run, and that each Player
# has had its leaderboard base fields updated.
def aggregateClanData():
    for clan in Clan.objects.all():
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
        clan.games_scummed = aggrs_dict['games_scummed__sum']
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

        # Unique ascs are still a one-liner.
        clan.unique_ascs = len(set(g.rrga() for g in gamesby_clan if g.won))

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
        # For clans, we have to remove all trophies before re-awarding them.
        # This is because a member who provided some of the effort towards a
        # trophy may have left since the last aggregation.
        clan.trophies.remove()
        awardTrophies(clan, gamesby_clan)
    logging.info('aggregateClanData complete')

class Command(BaseCommand):
    help = 'Compute aggregate data from the set of all games'

    # TODO: move most of this file's logic to tnnt/aggregate.py so that it can
    # be called on clan-membership-change events
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
