import io
from datetime import datetime, timedelta
from django.test import TestCase
from scoreboard.serializers import XlogRecordSerializer, XlogListSerializer, XlogParser
from scoreboard.models import Game, RecordSource, Player

class GameTest(TestCase):
    @classmethod
    def setUpClass(cls):
        self.src = RecordSource(
            server='hfe',
            variant='tnnt',
            description='whatever',
            local_file='hfe.xlog',
            last_check=datetime.now())

    def test_game(self):
        self.file = open('test.xlog',)
        data = XlogParser().parse(self.file)
        seri = XlogListSerializer(child=XlogRecordSerializer(), data=data)
        gameRecord = seri.save()
        game = Game(source=testLog, player=player, record=gameRecord).save()
