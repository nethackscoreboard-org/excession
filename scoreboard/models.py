from django.db import models

# Create your models here.
class GameRecord(models.Model):
    player_name = models.CharField(max_length=128)
    win = models.BooleanField(default=False)
    variant = models.CharField(max_length=128)
    version = models.CharField(max_length=128)
    death_reason = models.CharField(max_length=1024)


