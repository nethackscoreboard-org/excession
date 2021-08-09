import itertools
from rest_framework.response import Response
from rest_framework import status, viewsets, generics
from rest_framework.views import APIView
from .models import GameRecord
from .serializers import AscensionSerializer, GameSerializer

class RootEndpointList(generics.ListAPIView):
    def get(self, request):
        return Response({
            'links': {
                'ascended': '/ascended',
                'games': '/games',
                'players': '/players',
            }
        })

class AscendedList(generics.ListAPIView):
    def get(self, request):
        q = GameRecord.objects.filter(won=True)
        links = {}
        s = AscensionSerializer(q, many=True)
        return Response({'links': links, 'ascensions': s.data})

class GamesList(generics.ListAPIView):
    def get(self, request):
        q = GameRecord.objects.all()
        links = {}
        s = GameSerializer(q, many=True)
        return Response({'links': links, 'games': s.data})

class PlayersList(APIView):
    def get(self, request):
        q = GameRecord.objects.values('name').distinct()
        links = {}
        return Response({
            'links': links,
            'players': {r['name']: request.path + '/' + r['name'] for r in q}
        })

class NullPlayer(APIView):
    def get(self, request):
        q = GameRecord.objects.values('name').distinct()
        links = {}
        return Response({'error': 'no games by player ``'}, status=status.HTTP_404_NOT_FOUND)

class AscensionsByPlayerList(generics.ListAPIView):
    def get(self, request, player=None):
        if not player:
            return Response({'error': 'no player name given'}, status=status.HTTP_400_BAD_REQUEST)

        q = GameRecord.objects.filter(name=player)
        if not q.count():
            return Response({'error': 'no games by player `{}`'.format(player)}, status=status.HTTP_404_NOT_FOUND)

        links = {}
        s = AscensionSerializer(q, many=True)
        return Response({'links': links, 'ascensions': s.data})

class GamesByPlayerList(generics.ListAPIView):
    def get(self, request, player=None):
        if not player:
            return Response({'error': 'no player name given'}, status=status.HTTP_400_BAD_REQUEST)

        q = GameRecord.objects.filter(name=player)
        if not q.count():
            return Response({'error': 'no games by player `{}`'.format(player)}, status=status.HTTP_404_NOT_FOUND)

        links = {}
        wins = q.filter(won=True).count()
        if wins:
            links['ascended'] = request.path + player + '/ascended'
        s = GameSerializer(q, many=True)
        return Response({'links': links, 'games': s.data})