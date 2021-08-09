import re
from rest_framework import status
from django.test import TestCase, Client
from scoreboard.serializers import XlogListSerializer, XlogRecordSerializer, XlogParser

class APIViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        file = open('test.xlog',)
        parser = XlogParser()
        raw_data = parser.parse(file)
        serializer = XlogListSerializer(
            child=XlogRecordSerializer(),
            data=raw_data,
            context={'server': 'hdf', 'variant': 'tnnt'})
        serializer.is_valid()
        serializer.save()

    @classmethod
    def tearDownClass(cls) -> None:
        return super().tearDownClass()
    
    def test_root(self):
        c = Client()
        response = c.get('')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        links = response.data['links']
        for path in links.values():
            self.assertEqual(path[:1], '/', 'expect paths beginning with `/`')
        pass

    def test_ascended(self):
        c = Client()
        response = c.get('/ascended')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        self.assertEqual('ascensions' in response.data, True, 'expect an ascensions field')
        ascensions = response.data['ascensions']
        for win in ascensions:
            self.assertEqual('death' in win, False, 'ascended page doesn\'t show death reason')
            self.assertEqual('conducts' in win, True, 'ascended page shows conducts')

    def test_games(self):
        c = Client()
        response = c.get('/games')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        self.assertEqual('games' in response.data, True, 'expect a games field')
        games = response.data['games']
        for game in games:
            self.assertEqual('death' in game, True, 'games-list page shows death reason')
            self.assertEqual('conducts' in game, False, 'games-list page doesn\'t show conducts')

    def test_players(self):
        c = Client()
        response = c.get('/players')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        self.assertEqual('players' in response.data, True, 'expect a players field')
        players = response.data['players']
        for name, path in players.items():
            self.assertEqual(path, '/players/' + name, 'expect list of player names with paths to player pages')
        pass

    def test_null_player(self):
        c = Client()
        response = c.get('/players/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, 'player `` gives 404')
        pass

    def test_player_games(self):
        c = Client()
        response = c.get('/players/joo')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        self.assertEqual('games' in response.data, True, 'expect a games field')
        games = response.data['games']
        for game in games:
            self.assertEqual('death' in game, True, 'player games page shows death reason')
            self.assertEqual('conducts' in game, False, 'player games page doesn\'t show conducts')
        response = c.get('/players/joo')
        self.assertEqual('ascended' in response.data['links'], True, 'expect ascensions link')
        response = c.get('/players/thorsb')
        self.assertEqual('ascended' in response.data['links'], False, 'expect no ascensions link')
    
    def test_nonexistant_player(self):
        c = Client()
        response = c.get('/players/nobody')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, 'nonexistant player gives 404 error')
        pass

    def test_player_ascended(self):
        c = Client()
        response = c.get('/players/joo/ascended')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        self.assertEqual('ascensions' in response.data, True, 'expect an ascensions field')
        ascensions = response.data['ascensions']
        for ascension in ascensions:
            self.assertEqual('death' in ascension, False, 'ascended page doesn\'t show death reason')
            self.assertEqual('conducts' in ascension, True, 'ascended page shows conducts')
        pass