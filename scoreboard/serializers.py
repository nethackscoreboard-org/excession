from rest_framework import serializers
from .models import GameRecord

class GameRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRecord
        fields = [
            "player_name",
            "death_reason",
        ]
        extra_kwargs = {

        }