from django.db.models import fields
from .models import GameRecord, Conduct
from datetime import date, datetime, timedelta, timezone
import re
import itertools

WIZMODE_BITFLAG = 0x1
EXPLORE_BITFLAG = 0x2
BONESLESS_BITFLAG = 0x4

class XlogParser():
    required_fields = GameRecord.__required_fields__
    all_fields = GameRecord.__all_fields__
    metadata = {}
    conversions = {
        'datetime': lambda ts: datetime.fromtimestamp(int(ts), timezone.utc),
        'timedelta': lambda s: timedelta(seconds=int(s)),
        'int': lambda x: int(x),
        'hex': lambda x: int(x, 0),
    }
    fields_by_type = {
        'datetime': ['starttime', 'endtime'],
        'timedelta': ['realtime'],
        'int': ['turns', 'points'],
        'hex': ['flags', 'conduct', 'achieve', 'tnntachieve0', 'tnntachieve1', 'tnntachieve2', 'tnntachieve3'],
    }
    types_by_field = {}

    def __init__(self, server, variant='tnnt', delimiter="\t", separator="="):
        self.delimiter = delimiter
        self.separator = separator
        self.metadata['variant'] = variant
        self.metadata['server'] = server
        for key in self.fields_by_type:
            for field in self.fields_by_type[key]:
                self.types_by_field[field] = key
    
    def __squash__(self, record):
        return {f: record[f] for f in itertools.filterfalse(lambda k: k not in record, self.all_fields)}
    
    def __unpack__(self, line):
        return { k: v for k, v in [ i.split(self.separator) for i in line.split(self.delimiter) ] }
    
    def __are_all_required_fields_present__(self, fields):
        if [x for x in itertools.filterfalse(lambda k: k in fields, self.required_fields)]:
            return False
        else:
            return True
    
    def __convert__(self, record):
        for f in itertools.filterfalse(lambda k: k not in self.types_by_field, record):
            record[f] = self.conversions[self.types_by_field[f]](record[f])
    
    def __check_flags__(self, record):
        if 'flags' in record:
            flags = record['flags']
            if flags & WIZMODE_BITFLAG:
                record['wizmode'] = True
            if flags & EXPLORE_BITFLAG:
                record['explore'] = True
            if flags & BONESLESS_BITFLAG:
                record['bonesless'] = True
    
    def __parse_conducts__(self, record):
        conducts = []
        ach_conducts = []
        conduct_specs = Conduct.objects.filter(variant=record['variant'], version=record['version'], achieve_field=False)
        ach_conduct_specs = Conduct.objects.filter(variant=record['variant'], version=record['version'], achieve_field=True)
        if 'conduct' in record and conduct_specs:
            conducts = itertools.filterfalse(lambda c: not 1 << c.bit_index & record['conduct'], conduct_specs)
        if 'achieve' in record and ach_conduct_specs:
            ach_conducts = itertools.filterfalse(lambda c: not 1 << c.bit_index & record['achieve'], ach_conduct_specs)
        return conducts, ach_conducts

    def createGameRecord(self, xlog_line):
        if re.search('[\0\r\n]', xlog_line):
            raise ValueError

        record = {**self.metadata, **self.__unpack__(xlog_line)}

        if not self.__are_all_required_fields_present__(record.keys()):
            raise ValueError

        self.__convert__(record)
        self.__check_flags__(record)
        conducts, ach_conducts = self.__parse_conducts__(record)

        if record['starttime'] > datetime.now(tz=timezone.utc) or record['endtime'] > datetime.now(tz=timezone.utc):
            raise ValueError
        if record['starttime'] > record['endtime']:
            raise ValueError
        record['wallclock'] = record['endtime'] - record['starttime']
        if 'realtime' in record and record['wallclock'] < record['realtime']:
            raise ValueError

        parsed_record = GameRecord.objects.create(**self.__squash__(record))
        for conduct in conducts:
            parsed_record.conducts.add(conduct)
        for ach_conduct in ach_conducts:
            parsed_record.conducts.add(ach_conduct)
        parsed_record.save()
        return parsed_record
