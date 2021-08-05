from django.db import models

REQUIRED_GAME_RECORD_FIELDS = [
    'server',
    'variant',
    'version',
    'name',
    'death',
    'turns',
    'role',
    'starttime',
    'endtime',
    'turns',
]
OPTIONAL_GAME_RECORD_FIELDS = [
    'race',
    'win',
    'align',
    'gender',
    'align0',
    'gender0',
    'realtime',
    'wallclock',
    'points',
    'wizmode',
    'explore',
    'bonesless',
]

class Conduct(models.Model):
    unique_together = [['variant', 'version', 'bit_index']]
    variant    = models.CharField(max_length=128)
    version    = models.CharField(max_length=128)
    long_name  = models.CharField(max_length=128)
    short_name = models.CharField(max_length=16)
    bit_index  = models.IntegerField()

# Create your models here.
class GameRecord(models.Model):
    __required_fields__ = REQUIRED_GAME_RECORD_FIELDS
    __all_fields__      = REQUIRED_GAME_RECORD_FIELDS + OPTIONAL_GAME_RECORD_FIELDS

    server  = models.CharField(max_length=128)
    variant = models.CharField(max_length=128)

    version     = models.CharField(max_length=128)
    starttime   = models.DateTimeField()
    endtime     = models.DateTimeField()
    turns       = models.BigIntegerField()
    name        = models.CharField(max_length=128)
    death       = models.CharField(max_length=1024)
    role        = models.CharField(max_length=16)
    race        = models.CharField(max_length=16, null=True)
    align       = models.CharField(max_length=16, null=True)
    gender      = models.CharField(max_length=16, null=True)
    align0      = models.CharField(max_length=16, null=True)
    gender0     = models.CharField(max_length=16, null=True)
    points      = models.BigIntegerField(null=True)

    conducts    = models.ManyToManyField(Conduct)
    win         = models.BooleanField(default=False)
    wizmode     = models.BooleanField(default=False)
    explore     = models.BooleanField(default=False)
    bonesless   = models.BooleanField(default=False)
    realtime    = models.DurationField(null=True)
    wallclock   = models.DurationField(null=True)
