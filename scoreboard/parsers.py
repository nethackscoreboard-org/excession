from .models import GameRecord
import re

class XlogParser():
    variant = 'tnnt'
    required_xlog_fields = [ 'name', 'death', 'version' ]

    def __init__(self, delimiter="\t", separator="="):
        self.delimiter = delimiter
        self.separator = separator

    def createGameRecord(self, xlog_line):
        if re.search('[\0\r\n]', xlog_line):
            raise ValueError

        record = { k: v for k, v in [ i.split(self.separator) for i in xlog_line.split(self.delimiter) ] }
        for field in self.required_xlog_fields:
            if not field in record:
                raise ValueError
        kwargs = {
            'player_name': record['name'],
            'death_reason': record['death'],
            'variant': self.variant,
            'version': record['version'],
        }
        return GameRecord.objects.create(**kwargs)