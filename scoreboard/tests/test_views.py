from datetime import datetime, timedelta
from rest_framework import status
from django.test import TestCase, Client
from scoreboard.parsers import XlogListSerializer, XlogRecordSerializer, XlogParser

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
        ascensions = response.data['results']
        for win in ascensions:
            self.assertEqual('death' in win, False, 'ascended page doesn\'t show death reason')
            self.assertEqual('conducts' in win, True, 'ascended page shows conducts')

    def test_games(self):
        c = Client()
        response = c.get('/games?foo=bar')
        games = response.data['results']
        for game in games:
            self.assertEqual('death' in game, True, 'games-list page shows death reason')
            self.assertEqual('conducts' in game, False, 'games-list page doesn\'t show conducts')

    def test_players(self):
        c = Client()
        response = c.get('/players')
        players = response.data['results']
        names = []
        for entry in players:
            for name, path in entry.items():
                self.assertEqual(path, '/players/' + name, 'expect list of player names with paths to player pages')
                self.assertEqual(name in names, False, 'names should appear only once')
                names.append(name)
        pass

    def test_player_games(self):
        c = Client()
        response = c.get('/players/joo')
        games = response.data['results']
        for game in games:
            self.assertEqual('death' in game, True, 'player games page shows death reason')
            self.assertEqual('conducts' in game, False, 'player games page doesn\'t show conducts')

    def test_player_ascended(self):
        c = Client()
        response = c.get('/players/joo/ascended')
        ascensions = response.data['results']
        for ascension in ascensions:
            self.assertEqual('death' in ascension, False, 'ascended page doesn\'t show death reason')
            self.assertEqual('conducts' in ascension, True, 'ascended page shows conducts')
        pass

    def test_leaderboards(self):
        c = Client()
        response = c.get('/leaderboards')
        self.assertEqual('links' in response.data, True, 'expect a links field')
        links = response.data['links']
        self.assertEqual('realtime' in links, True, 'expect a realtime leaderboard link')
        pass

    def test_leaderboards_realtime(self):
        c = Client()
        response = c.get('/leaderboards/realtime')
        pbs = response.data['results']
        prev_time = timedelta(seconds=0)
        names = []
        for win in pbs:
            time = timedelta(seconds=int(win['realtime']))
            self.assertEqual(time < prev_time, False, 'entries should be sorted in ascending order by duration')
            prev_time = time
            self.assertEqual(win['name'] in names, False, 'a given player should appear no more than once')
            names.append(win['name'])
        pass