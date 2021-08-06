from scoreboard.serializers import XlogListSerializer, XlogRecordSerializer, XlogParser
from scoreboard.views import ListAscensions
from django.test import TestCase

class AscendedViewSetTest(TestCase):
    def setUp(self):
        file = open('tnnt-2020-eu',)
        parser = XlogParser()
        raw_data = parser.parse(file)
        serializer = XlogListSerializer(
            child=XlogRecordSerializer(),
            data=raw_data,
            context={'server': 'hdf', 'variant': 'tnnt'})
        serializer.is_valid()
        serializer.save()
    
    def test_list_ascensions(self):
        pass