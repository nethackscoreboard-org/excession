from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import serializers, status, viewsets, generics
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
                'leaderboards': '/leaderboards',
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

class LeaderboardsList(APIView):
    def get(self, request):
        q = GameRecord.objects.values('name').distinct()
        links = {
            'realtime': request.path + '/' + 'realtime',
            'wallclock': request.path + '/' + 'wallclock',
            'conducts': request.path + '/' + 'conducts',
        }
        return Response({
            'links': links,
        })

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

class NullView(APIView):
    def get(self, request):
        return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

class RealtimeBoard(APIView):
    def get(self, request):
        players = list(OrderedDict.fromkeys([
            p['name'] for p in
            GameRecord.objects.filter(won=True).order_by('realtime').values('name')
        ]))
        links = {}
        pbs = [GameRecord.objects.filter(won=True, name=p).order_by('realtime').first() for p in players]
        s = AscensionSerializer(pbs, many=True)
        return Response({'links': links, 'player_bests': s.data})

class WallclockBoard(APIView):
    def get(self, request):
        players = list(OrderedDict.fromkeys([
            p['name'] for p in
            GameRecord.objects.filter(won=True).order_by('wallclock').values('name')
        ]))
        links = {}
        pbs = [GameRecord.objects.filter(won=True, name=p).order_by('wallclock').first() for p in players]
        s = AscensionSerializer(pbs, many=True)
        return Response({'links': links, 'player_bests': s.data})

class ConductsBoard(APIView):
    def get(self, request):
        players = list(OrderedDict.fromkeys([
            p['name'] for p in
            GameRecord.objects.filter(won=True).order_by('-nconducts').values('name')
        ]))
        links = {}
        pbs = [GameRecord.objects.filter(won=True, name=p).order_by('-nconducts').first() for p in players]
        s = AscensionSerializer(pbs, many=True)
        return Response({'links': links, 'player_bests': s.data})

class TurncountBoard(APIView):
    def get(self, request):
        players = list(OrderedDict.fromkeys([
            p['name'] for p in
            GameRecord.objects.filter(won=True).order_by('turns').values('name')
        ]))
        links = {}
        pbs = [GameRecord.objects.filter(won=True, name=p).order_by('turns').first() for p in players]
        s = AscensionSerializer(pbs, many=True)
        return Response({'links': links, 'player_bests': s.data})