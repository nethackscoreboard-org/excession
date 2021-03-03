#import pycurl
from django.utils import timezone
from sys import stderr
from datetime import datetime
from .models import LogSource, Game
from . import nh

"""
to test, run python manage.py shell, then enter:
import scoreboard.xlog
scoreboard.xlog.try_file_read("xlogs/xlogfile-eu-2020", "eu2020")
"""

convert = dict.fromkeys(
    ('points', 'maxlvl', 'hp', 'maxhp', 'deaths', 'turns', 'realtime', 'deathdnum', 'deaths', 'deathlev'),
    lambda x: int(x))
#convert.update(dict.fromkeys(
#    ('conduct', 'flags', 'achieve', 'tnntachieve0', 'tnntachieve1', 'tnntachieve2', 'tnntachieve3'),
#    lambda x: int(x, 16)))
convert.update(dict.fromkeys(
    ('birthdate', 'deathdate'),
    lambda x: datetime.strptime(x, "%Y%m%d").date()))
convert.update(dict.fromkeys(
    ('starttime', 'endtime'),
    lambda x: datetime.fromtimestamp(int(x), timezone.utc)))
convert.update(dict.fromkeys(
    ('death'),
    lambda x: x))
linked_fields = ['version', 'role', 'race', 'align', 'align0', 'gender', 'gender0']

def parse(line, src):
    record = {}
    for key, value in map(lambda x: x.split('=', 1), line.split('\t')):
        if key in convert:
            record[key] = convert[key](value)
        elif key in linked_fields:
            record[key] = nh.lookup(key, value)
#        else:
#            print(f"unhandled xlog field {key}\n", file=stderr)
    return Game(**record, source=src)

def parse_records(f, src):
    count = 0
    for line in f.readlines():
        if count > 10:
            break
        game = parse(line, src)
        game.save()
        count += 1
    return count

def try_file_read(path, src):
    src = LogSource.objects.get(src_name=src)
    with open(path, "r") as f:
        print(f"records read/processed: {parse_records(f, src)}\n")


#def fetch_sources():
#    for src in LogSource.objects.all():
#        with open(src.local_path, 'wb') as f:
#            c = pycurl.Curl()
#            c.setopt(c.URL, src)
#            c.setopt(c.WRITEDATA, f)
#            c.perform()
#            c.close()
#        with open(src.local_path, 'rb') as f:
#            f.seek(src.file_cursor, 0)
#            src.records_imported += parse_records(f)
#            src.file_cursor = f.tell()
#            src.last_check = timezone.now()
#            src.save()

