from django.db import models
from tnnt import settings

class Clan(models.Model):
    name = models.CharField(max_length=128)

class GameRecord(models.Model):
    GameMode     = models.TextChoices('GameMode', 'normal explore polyinit hah wizard')
    version      = models.CharField(max_length=128)
    name         = models.CharField(max_length=128)
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
    death        = models.CharField(max_length=1024)
    align0       = models.CharField(max_length=16, null=True)
    gender0      = models.CharField(max_length=16, null=True)
    conducts     = models.CharField(max_length=4096, null=True, default='')
    nconducts    = models.IntegerField(default=0)
    achievements = models.CharField(max_length=4096, null=True, default='')
    won          = models.BooleanField(default=False)
    bonesless    = models.BooleanField(default=False)
    mode         = models.CharField(choices=GameMode.choices, default='normal', max_length=16)

class RecordSource(models.Model):
    server      = models.CharField(max_length=128)
    variant     = models.CharField(max_length=128)
    description = models.CharField(max_length=256)
    local_file  = models.FilePathField(path=settings.XLOG_DIR)
    file_pos    = models.BigIntegerField()
    last_check  = models.DateTimeField()
    location    = models.URLField(null=True)
    website     = models.URLField(null=True)
    dumplog_fmt = models.CharField(max_length=128)

class Player(models.Model):
    name = models.CharField(max_length=128)
    clan = models.ForeignKey(Clan, on_delete=models.CASCADE)

class Game(GameRecord):
    source = models.ForeignKey(RecordSource, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    record = models.OneToOneField(GameRecord, on_delete=models.CASCADE)
