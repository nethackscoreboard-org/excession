from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta, timezone
from tnnt import settings

# If adding any more models to this file, be sure to add a deletion for them in
# wipe_db.py.

class Trophy(models.Model):
    # The "perma-trophy" structure. Loaded from config.
    name        = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=128)

class Conduct(models.Model):
    # The "perma-conduct" structure. Loaded from config.
    name      = models.CharField(max_length=64, unique=True)
    shortname = models.CharField(max_length=4, unique=True)

    # the xlog field name this achievement is encoded with
    # "conduct" in most cases but blind and nudist use "achieve"...
    xlogfield = models.CharField(max_length=16)
    # xlog bit position this conduct occupies in the "conduct" xlog field
    # (assuming "1 << bit")
    bit       = models.IntegerField()

    class Meta:
        # no two conducts should have the same xlogfield and bit
        unique_together = ('xlogfield', 'bit')

class Achievement(models.Model):
    # The "perma-achievement" structure. Loaded from config.
    name        = models.CharField(max_length=128)
    description = models.CharField(max_length=128)
    # TODO (post 2021): possibly an int primary key or string id for this, so it
    # can be shown with the achievement and matches the one shown in-game

    # the xlog field name this achievement is encoded with
    # "achieve", "tnntachieveX", etc
    xlogfield   = models.CharField(max_length=16)
    # xlog bit position this conduct occupies (assuming "1 << bit")
    bit         = models.IntegerField()

    class Meta:
        # no two achievements should have the same xlogfield and bit
        unique_together = ('xlogfield', 'bit')

class LeaderboardBaseFields(models.Model):
    # Abstract base class that provides leaderboard-related fields that both
    # Player and Clan use. Does not have a table in the database.
    class Meta:
        abstract = True

    # Most/all of these are set in the aggregation step, after xlog data has
    # been read into the database but before it's ready for consumption.
    longest_streak         = models.IntegerField(default=0)
    unique_deaths          = models.IntegerField(default=0)
    unique_ascs            = models.IntegerField(default=0)
    unique_achievements    = models.IntegerField(default=0)
    games_over_1000_turns  = models.IntegerField(default=0)
    games_scummed          = models.IntegerField(default=0)
    total_games            = models.IntegerField(default=0)
    wins                   = models.IntegerField(default=0)
    lowest_turncount_asc   = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')
    fastest_realtime_asc   = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')
    max_conducts_asc       = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')
    max_achieves_game      = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')
    min_score_asc          = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')
    max_score_asc          = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')
    first_asc              = models.ForeignKey('Game', null=True, on_delete=models.SET_NULL, related_name='+')

class Clan(LeaderboardBaseFields):
    name     = models.CharField(max_length=128, unique=True)
    # clan admin can configure message
    message  = models.CharField(max_length=512, default='')
    # perhaps trophies could go in LeaderboardBaseFields but it's not actually a
    # leaderboard field so keeping it conceptually separate makes sense for now
    trophies = models.ManyToManyField(Trophy)
    # FUTURE TODO: perhaps there should be:
    # admins = models.ManyToManyField(Player)
    # instead of Player having a clan_admin field

class Streak:
    # This is NOT a database model!
    # It is a simple storage class for streak information that can be used in
    # aggregation and relayed to the frontend.

    def __init__(self, singlegame):
        self.games       = [ singlegame ] # list of Games in the streak
        self.continuable = True           # whether it can be continued

class AscendingPlayersManager(models.Manager):
    # Manager that returns only Players with at least one ascension, which is a
    # pretty common request.
    def get_queryset(self):
        return super().get_queryset().filter(wins__gt=0)

class Player(LeaderboardBaseFields):
    name       = models.CharField(max_length=32, unique=True)
    clan       = models.ForeignKey(Clan, null=True, on_delete=models.SET_NULL)
    trophies   = models.ManyToManyField(Trophy)
    clan_admin = models.BooleanField(default=False)
    invites    = models.ManyToManyField(Clan, related_name='invitees')
    # link to User model for web logins
    user       = models.OneToOneField(User, on_delete=models.PROTECT, null=True)

    objects   = models.Manager() # default
    ascenders = AscendingPlayersManager()

    # Return a string denoting the ascension ratio of this player.
    # This can assume that total_games > 0, but wins could be 0.
    def ratio(self):
        return '{:.2f}%'.format(self.wins * 100 / self.total_games)

    # Compute this player's streaks, and return them as a list of Streaks
    # containing the games in the streak and whether they can be continued.
    def get_streaks(self):
        # Due to multiple servers, start and end times can overlap. The
        # candidate game for continuing a streak is the first one started after
        # an ascension.
        # If a game is eligible to continue MULTIPLE streaks at once (possible
        # with server shenanigans), it will continue only the oldest of those
        # streaks (i.e. the one that comes first in streaks), and kill the rest
        # (TODO: write this explicitly in the rules.)
        # ASSUMPTION: No two Games of the same player will ever have the same
        # starttime. If they did, it would be possible to have two candidate
        # games for continuing the streak and not know which one to count.

        streaks = []
        for g in Game.objects.filter(player=self).order_by('starttime').all():
            extended_or_killed_streak = False
            # first: will this game extend/kill a streak?
            for strk in streaks:
                if strk.continuable == False:
                    # this streak is dead, ignore it
                    continue
                if strk.games[-1].endtime < g.starttime:
                    extended_or_killed_streak = True
                    if g.won == False:
                        # streak is killed
                        strk.continuable = False
                        continue # it could still kill other streaks
                    else:
                        # streak is extended
                        strk.games.append(g)
                        # and stop looking for other streaks to extend
                        break

            # if we didn't extend or kill a streak, and the game is a win, we start one
            if (not extended_or_killed_streak) and g.won:
                streaks.append(Streak(g))

        # filter out "streaks" of only 1 game, which are not streaks yet
        return [ strk for strk in streaks if len(strk.games) >= 2 ]

class Source(models.Model):
    # Information about a source of aggregate game data (e.g. an xlogfile).
    server      = models.CharField(max_length=32, unique=True)
    local_file  = models.FilePathField(path=settings.XLOG_DIR)
    file_pos    = models.BigIntegerField(default=0)
    last_check  = models.DateTimeField()
    location    = models.URLField(null=True)

    # dumplog_fmt uses a few custom format specifiers which are intended to be
    # server-agnostic. Currently these are:
    # %n1 - first character of the player's name.
    # %n  - player's full name.
    # %st - game start timestamp.
    dumplog_fmt = models.CharField(max_length=128)

    # These fields are more NHS specific (not relevant to tnnt).
    # variant     = models.CharField(max_length=32)
    # description = models.CharField(max_length=256)
    # website     = models.URLField(null=True)

class GameManager(models.Manager):
    simple_fields = ['version', 'role', 'race', 'gender', 'align', 'points', 'turns', 'realtime', 'maxlvl', 'death',
                     'align0', 'gender0']

    def from_xlog(self, source, xlog_dict):
        # TODO: validate xlog_dict contains some set of 'required_fields'
        # simple fields get keyed directly to keyword args to self.create()
        kwargs = {'source': source}
        for key in self.simple_fields:
            kwargs[key] = xlog_dict[key]

        # filter explore/wizmode games
        # TODO: do something about magic numbers in this method
        if xlog_dict['flags'] & 0x1 or xlog_dict['flags'] & 0x2:
            return

        # assign 'won' boolean
        # TODO: do something about magic numbers in this method
        if xlog_dict['achieve'] & 0x100:
            kwargs['won'] = True

        # time/duration information
        kwargs['starttime'] = datetime.fromtimestamp(xlog_dict['starttime'], timezone.utc)
        kwargs['endtime'] = datetime.fromtimestamp(xlog_dict['endtime'], timezone.utc)
        kwargs['realtime'] = timedelta(seconds=xlog_dict['realtime'])
        kwargs['wallclock'] = kwargs['endtime'] - kwargs['starttime']

        # TODO: filter games here based on starttime and endtime being outside
        # of the configured starttime and endtime for the tournament

        # find/create player
        try:
            player = Player.objects.get(name=xlog_dict['name'])
        except Player.DoesNotExist:
            player = Player(name=xlog_dict['name'], clan=None, clan_admin=False)
            player.save()
        kwargs['player'] = player

        game = self.create(**kwargs)
        for conduct in Conduct.objects.all():
            if conduct.xlogfield in xlog_dict and xlog_dict[conduct.xlogfield] & (1 << conduct.bit):
                game.conducts.add(conduct)
        for achieve in Achievement.objects.all():
            if achieve.xlogfield in xlog_dict and xlog_dict[achieve.xlogfield] & (1 << achieve.bit):
                game.achievements.add(achieve)

        return game

class Game(models.Model):
    # Represents a single game: a single line in the xlog, a single dumplog, etc.
    # The following fields are those drawn directly from the xlogfile:
    # polyinit and hah don't exist in tnnt, explore/wizmode games will just be discarded
    # GameMode     = models.TextChoices('GameMode', 'normal explore polyinit hah wizard')
    version      = models.CharField(max_length=32)
    role         = models.CharField(max_length=16)
    race         = models.CharField(max_length=16, null=True)
    gender       = models.CharField(max_length=16, null=True)
    align        = models.CharField(max_length=16, null=True)

    # these are handled as python ints in an intermediate step
    # TODO: check: how big are python ints?
    # TODO: rename points => score
    points       = models.BigIntegerField(null=True)
    turns        = models.BigIntegerField()

    # NOTE: All the "fastest realtime" code uses wallclock, NOT realtime
    realtime     = models.DurationField(null=True)
    wallclock    = models.DurationField(null=True)
    maxlvl       = models.IntegerField(null=True)
    starttime    = models.DateTimeField()
    endtime      = models.DateTimeField()
    death        = models.CharField(max_length=256)
    align0       = models.CharField(max_length=16, null=True)
    gender0      = models.CharField(max_length=16, null=True)
    won          = models.BooleanField(default=False)

    # not necessary for tnnt but may re-introduce for NHS
    # deathlev     = models.IntegerField(null=True)
    # hp           = models.BigIntegerField(null=True)
    # maxhp        = models.BigIntegerField(null=True)
    # tracked as a conduct in nh-tnnt
    # bonesless    = models.BooleanField(default=False)

    # here are fields that indirectly come from the xlogfile but relate to other
    # models in the database; for instance player corresponds to 'name' in xlog
    player       = models.ForeignKey(Player, on_delete=models.CASCADE)
    conducts     = models.ManyToManyField(Conduct)
    achievements = models.ManyToManyField(Achievement)
    source       = models.ForeignKey(Source, on_delete=models.PROTECT)

    # this allows the GameManager class to handle creation of new Game objects,
    # using Game.objects.from_xlog()
    objects = GameManager()

    # Return a URL to the dumplog of this game.
    # ASSUMPTION: No two Games of the same player will have the same starttime.
    def get_dumplog(self):
        return self.source.dumplog_fmt \
            .replace('%n1', self.player.name[0]) \
            .replace('%n', self.player.name) \
            .replace('%st', str(int(self.starttime.timestamp())))

    # Return a string containing this game's conducts in human readable form
    # e.g. "poly wish veg"
    def conducts_as_str(self):
        return ' '.join(c.shortname for c in self.conducts.all())

    # Return a string of the form "Rol-Rac-Gen-Aln" typical in nethack parlance.
    # Importantly, this uses gender0 and align0.
    def rrga(self):
        return '-'.join([self.role, self.race, self.gender0, self.align0])


