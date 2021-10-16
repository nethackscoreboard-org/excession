from django.db import models
from django.contrib.auth.models import User
from tnnt import settings

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
    name        = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=128)

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

    # These are all nullable, because a Player or Clan can exist with no games
    # (i.e. during pre tournament registration).
    lowest_turncount       = models.IntegerField(null=True)
    fastest_realtime       = models.DurationField(null=True)
    max_conducts_in_1_game = models.IntegerField(null=True)
    max_ach_in_1_game      = models.IntegerField(null=True)
    min_score              = models.IntegerField(null=True)
    max_score              = models.IntegerField(null=True)
    longest_streak         = models.IntegerField(null=True)
    earliest_asc_time      = models.DateTimeField(null=True)
    unique_deaths          = models.IntegerField(null=True)
    unique_ascs            = models.IntegerField(null=True)
    games_over_1000_turns  = models.IntegerField(null=True)

class Clan(LeaderboardBaseFields):
    name     = models.CharField(max_length=128, unique=True)
    # clan admin can configure message
    message  = models.CharField(max_length=512, default='')
    # perhaps trophies could go in LeaderboardBaseFields but it's not actually a
    # leaderboard field so keeping it conceptually separate makes sense for now
    trophies = models.ManyToManyField(Trophy)

class Player(LeaderboardBaseFields):
    name       = models.CharField(max_length=32, unique=True)
    clan       = models.ForeignKey(Clan, null=True, on_delete=models.SET_NULL)
    trophies   = models.ManyToManyField(Trophy)
    clan_admin = models.BooleanField(default=False)
    invites    = models.ManyToManyField(Clan, related_name='invitees')
    # link to User model for web logins
    user       = models.OneToOneField(User, on_delete=models.PROTECT, null=True)

class Source(models.Model):
    # Information about a source of aggregate game data (e.g. an xlogfile).
    server      = models.CharField(max_length=32, unique=True)
    local_file  = models.FilePathField(path=settings.XLOG_DIR)
    file_pos    = models.BigIntegerField()
    last_check  = models.DateTimeField()
    location    = models.URLField(null=True)
    website     = models.URLField(null=True)

    # These fields are more NHS specific (not relevant to tnnt).
    # variant     = models.CharField(max_length=32)
    # description = models.CharField(max_length=256)
    # dumplog_fmt = models.CharField(max_length=128)

class Game(models.Model):
    # Represents a single game: a single line in the xlog, a single dumplog, etc.
    # The following fields are those drawn directly from the xlogfile:
    GameMode     = models.TextChoices('GameMode', 'normal explore polyinit hah wizard')
    version      = models.CharField(max_length=32)
    role         = models.CharField(max_length=16)
    race         = models.CharField(max_length=16, null=True)
    gender       = models.CharField(max_length=16, null=True)
    align        = models.CharField(max_length=16, null=True)
    points       = models.BigIntegerField(null=True)
    turns        = models.BigIntegerField()
    realtime     = models.DurationField(null=True)
    wallclock    = models.DurationField(null=True)
    deathlev     = models.IntegerField(null=True)
    maxlvl       = models.IntegerField(null=True)
    hp           = models.BigIntegerField(null=True)
    maxhp        = models.BigIntegerField(null=True)
    starttime    = models.DateTimeField()
    endtime      = models.DateTimeField()
    death        = models.CharField(max_length=256)
    align0       = models.CharField(max_length=16, null=True)
    gender0      = models.CharField(max_length=16, null=True)
    # note: "won" is technically redundant since death=="ascended" but it may be
    # faster to store this as a boolean?
    won          = models.BooleanField(default=False)
    bonesless    = models.BooleanField(default=False)

    # here are fields that indirectly come from the xlogfile but relate to other
    # models in the database; for instance player corresponds to 'name' in xlog
    player       = models.ForeignKey(Player, on_delete=models.CASCADE)
    conducts     = models.ManyToManyField(Conduct)
    achievements = models.ManyToManyField(Achievement)
    # TODO: should this key to the server field or some such?
    source       = models.ForeignKey(Source, on_delete=models.PROTECT)

