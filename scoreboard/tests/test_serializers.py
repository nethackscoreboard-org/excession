import io
from datetime import datetime, timedelta
from django.test import TestCase
from rest_framework import serializers
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

    def test_future_starttime(self):
        raw_data = self.parser.parse(self.file)[0]
        raw_data['starttime'] = int((datetime.now() + timedelta(days=1)).timestamp())
        raw_data['endtime'] = int((datetime.now() + timedelta(days=2)).timestamp())
        serializer = XlogRecordSerializer(data=raw_data, context={'server': 'hdf', 'variant': 'tnnt'})
        self.assertEqual(serializer.is_valid(), False)
        pass

    def test_future_endtime(self):
        raw_data = self.parser.parse(self.file)[0]
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
        pass
    
#    def test_won(self):
#        params =  {'achieve': '0x100'}
#        game_record = self.parser.createGameRecord(gen_xlog(params))
#        self.assertEqual(game_record.won, True)
#        params =  {'death': 'ascended'}
#        game_record = self.parser.createGameRecord(gen_xlog(params))
#        self.assertEqual(game_record.won, True)
#        params =  {'death': 'foobar', 'achieve': '0x00'}
#        game_record = self.parser.createGameRecord(gen_xlog(params))
#        self.assertEqual(game_record.won, False)
    
