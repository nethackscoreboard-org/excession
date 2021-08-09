from scoreboard.serializers import XlogListSerializer, XlogRecordSerializer, XlogParser

class TestData:
    def import_and_save_from_xlogfile(self, filename):
        file = open(filename,)
        parser = XlogParser()
        raw_data = parser.parse(file)
        serializer = XlogListSerializer(
            child=XlogRecordSerializer(),
            data=raw_data,
            context={'server': 'hdf', 'variant': 'tnnt'})
        serializer.is_valid()
        serializer.save()