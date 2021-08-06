import itertools
from django.urls import reverse
from rest_framework.response import Response
from rest_framework import serializers, viewsets, generics
from rest_framework.views import APIView
from .models import GameRecord
from .serializers import GameSerializer

class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameRecord.objects.all()
    serializer_class = GameSerializer

class AscendedViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GameRecord.objects.filter(won=True)
    serializer_class = GameSerializer

class PlayersList(APIView):
    def get(self, request):
        q = GameRecord.objects.values('name').distinct()
        url = reverse('players-list')
        return Response({r['name']: {'url': '{}{}'.format(url, r['name'])} for r in q})

class GamesByPlayerList(generics.ListAPIView):
    serializer_class = GameSerializer

    def get_queryset(self):
        return GameRecord.objects.filter(name=self.kwargs['player'])