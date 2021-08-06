import itertools
from rest_framework.response import Response
from rest_framework import serializers, viewsets
from .models import GameRecord
from .serializers import SimpleGameSerializer

class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameRecord.objects.all()
    serializer_class = SimpleGameSerializer

class AscendedViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameRecord.objects.filter(won=True)
    serializer_class = SimpleGameSerializer

class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameRecord.objects.all()
    serializer_class = SimpleGameSerializer

    def list(self, query):
        q = GameRecord.objects.values('name').distinct()
        return Response({r['name']: {'url': '/rs/players/{}'.format(r['name'])} for r in q})