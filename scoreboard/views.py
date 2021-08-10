from collections import OrderedDict
from rest_framework import status, generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import GameRecord
from .serializers import AscensionSerializer, GameSerializer, PlayerLinkSerializer

class RootEndpointList(APIView):
    def get(self, request):
        return Response({
            'links': {
                'ascended': '/ascended',
                'games': '/games',
                'players': '/players',
                'leaderboards': '/leaderboards',
            }
        })

class GamesList(generics.ListAPIView):
    pagination_class = LimitOffsetPagination
    serializer_class = GameSerializer
    
    def get_queryset(self):
        if 'player' in self.kwargs:
            return GameRecord.objects.filter(name=self.kwargs['player'])
        else:
            return GameRecord.objects.all()

class AscendedList(GamesList):
    serializer_class = AscensionSerializer

    def get_queryset(self):
        if 'player' in self.kwargs:
            return GameRecord.objects.filter(won=True, name=self.kwargs['player'])
        else:
            return GameRecord.objects.filter(won=True)

class LeaderboardsList(APIView):
    def get(self, request):
        links = {
            'conducts': request.path + '/' + 'conducts',
            'minscore': request.path + '/' + 'minscore',
            'realtime': request.path + '/' + 'realtime',
            'turncount': request.path + '/' + 'turncount',
            'wallclock': request.path + '/' + 'wallclock',
        }
        return Response({
            'links': links,
        })

class PlayersList(generics.ListAPIView):
    pagination_class = LimitOffsetPagination
    serializer_class = PlayerLinkSerializer
    queryset = GameRecord.objects.values('name').distinct()

class Leaderboard(generics.ListAPIView):
    pagination_class = LimitOffsetPagination
    serializer_class = AscensionSerializer
    sort_field = None

    def get_queryset(self):
        players = list(OrderedDict.fromkeys([
            p['name'] for p in
            GameRecord.objects.filter(won=True).order_by(self.sort_field).values('name')
        ]))
        return [GameRecord.objects.filter(won=True, name=p).order_by(self.sort_field).first() for p in players]

class ConductsBoard(Leaderboard):
    sort_field = '-nconducts'

class MinscoreBoard(Leaderboard):
    sort_field = 'points'

class RealtimeBoard(Leaderboard):
    sort_field = 'realtime'

class TurncountBoard(Leaderboard):
    sort_field = 'turns'

class WallclockBoard(Leaderboard):
    sort_field = 'wallclock'