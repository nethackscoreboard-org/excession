from scoreboard.serializers import SimpleGameSerializer
from scoreboard.models import GameRecord
from rest_framework import serializers, viewsets
from .models import GameRecord

class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameRecord.objects.all()
    serializer_class = SimpleGameSerializer