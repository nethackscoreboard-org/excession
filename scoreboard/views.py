from scoreboard.models import GameRecord
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import GameRecord

class ListGames(APIView):
    def get(self, request, format=None):
        return Response(GameRecord.objects.all())