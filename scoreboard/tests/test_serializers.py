import io
from datetime import datetime, timedelta
from django.test import TestCase
from scoreboard.serializers import XlogListSerializer, XlogRecordSerializer, XlogParser

class XlogParserTest(TestCase):
    def setUp(self):
        self.file = open('test.xlog',)
        self.parser = XlogParser()
    
    def test_xlog_parser(self):
        raw_data = self.parser.parse(self.file)
        serializer = XlogListSerializer(child=XlogRecordSerializer(), data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        serializer.save()

    def test_missing_required_fields(self):
        raw_data = self.parser.parse(io.StringIO("death=ascended\thp=24\n"))
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), False)
        pass

    def test_starttime_after_endtime(self):
        raw_data = self.parser.parse(self.file)[0]
        raw_data['starttime'] = int(datetime.now().timestamp())
        raw_data['endtime'] = int((datetime.now() - timedelta(days=5)).timestamp())
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), False)
        pass

    def test_realtime_greater_than_wallclock(self):
        raw_data = self.parser.parse(self.file)[0]
        raw_data['realtime'] = 40000
        raw_data['starttime'] = int((datetime.now() - timedelta(seconds=100)).timestamp())
        raw_data['endtime'] = int((datetime.now() - timedelta(seconds=5)).timestamp())
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), False)
        pass

    def test_future_times(self):
        raw_data = self.parser.parse(self.file)[0]
        raw_data['starttime'] = int((datetime.now() + timedelta(days=1)).timestamp())
        raw_data['endtime'] = int((datetime.now() + timedelta(days=2)).timestamp())
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), False)
        raw_data['starttime'] = int((datetime.now() - timedelta(days=1)).timestamp())
        raw_data['endtime'] = int((datetime.now() + timedelta(days=2)).timestamp())
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), False)
        pass

    def test_flags(self):
        raw_data = self.parser.parse(self.file)[0]
        raw_data['flags'] = 0x4
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        game = serializer.save()
        self.assertEqual(game.bonesless, True)
        raw_data['flags'] = 0x6
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        game = serializer.save()
        self.assertEqual(game.mode, 'explore')
        self.assertEqual(game.bonesless, True)
        raw_data['flags'] = 0x1
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        game = serializer.save()
        self.assertEqual(game.mode, 'wizard')
        pass

    def test_conducts(self):
        raw_data = self.parser.parse(self.file)[0]
        raw_data['conduct'] = 0x1800
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        game = serializer.save()
        self.assertEqual('elberethless' in game.conducts.split(','), True)
        self.assertEqual('genocideless' in game.conducts.split(','), True)
        self.assertEqual('atheist' in game.conducts.split(','), False)
        raw_data['conduct'] = 0x6
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        game = serializer.save()
        self.assertEqual('vegan' in game.conducts.split(','), True)
        self.assertEqual('vegetarian' in game.conducts.split(','), True)
        self.assertEqual('wishless' in game.conducts.split(','), False)
        raw_data['achieve'] = 0x1000
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), True)
        game = serializer.save()
        self.assertEqual('blind' in game.conducts.split(','), True)
        pass
    
#    def test_won(self):
    
