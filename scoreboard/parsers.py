from rest_framework.parsers import BaseParser

dec_fields = ['points', 'turns', 'realtime', 'maxlvl', 'starttime', 'endtime']
hex_fields = [
    'flags', 'achieve', 'conduct', 'tnntachieve0', 'tnntachieve1', 'tnntachieve2', 'tnntachieve3', 'tnntachieve4'
]


def convert_if_numeric(key, value):
    if key in dec_fields:
        return int(value, 10)
    elif key in hex_fields:
        return int(value, 16)
    else:
        return value


class XlogParser(BaseParser):
    delimiter = '\t'
    separator = '='

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
                k: convert_if_numeric(k, v)
                for k, v in [
                    i.split(self.separator)
                    for i in line.rstrip().split(self.delimiter)
                ]
            }
            for line in stream.readlines()
        ]