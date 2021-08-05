import json
import math
from scoreboard.models import Achievement

def load_achievements():
    data = open('scripts/tnnt_achievements.json',)
    data = json.load(data)
    for value in data.values():
      xlog_field = [k for k in value.keys()][0]
      bit_index = int(math.log(int(value[xlog_field], 0), 2))
      Achievement.objects.create(variant='tnnt', version='3.6.6', xlog_field=xlog_field, bit_index=bit_index, title=value['title'], description=value['descr'])

