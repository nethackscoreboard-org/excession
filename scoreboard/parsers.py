from django.db.models import fields
from rest_framework.parsers import BaseParser
from rest_framework import serializers
from datetime import date, datetime, timedelta, timezone
from scoreboard.models import Game
import re

class XlogParser(BaseParser):
    delimiter = '\t'
    separator = '='

    def __convert__(self, value):
        if re.match('^[0-9]+$', value) or re.match('^0x[0-9a-fA-F]+$', value):
            return int(value, 0)
        else:
            return value

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parse xlogfile data into python primitive types.
        This step is required before the XlogListSerializer and XlogRecordSerializer
        can do their jobs.
        Input: filehandle stream e.g. from fopen('foo.xlog',)
        Output: list of dicts xlog_entry, where
        xlog entry = { key: val, ... } for each xlogfile field `<key>=<val>`, where
        each numeric value is converted to an integer with int(val, 0). This could
        possibly cause issues with fields where we're using bigint in the database...
        """
        return [
            {
                k: self.__convert__(v)
                for k, v in [
                    i.split(self.separator)
                    for i in line.rstrip().split(self.delimiter)
                ]
            }
            for line in stream.readlines()
        ]