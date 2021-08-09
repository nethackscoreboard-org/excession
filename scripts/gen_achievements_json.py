import json
import math

try:
  file_in = open('scripts/tnnt_achievements.json',)
  data_in = json.load(file_in)
except:
  print("couldn't open scripts/tnnt_achievements.json to read")
  exit(1)

data_out = {}
for value in data_in.values():
  xlog_field = [k for k in value.keys()][0]
  if not xlog_field in data_out:
    data_out[xlog_field] = {}
  bit = int(value[xlog_field], 0)
  title = value['title']
  descr = value['descr']
  data_out[xlog_field][hex(bit)] = {title: descr}

try:
  file_out = open('scoreboard/data/achievements.json', 'w')
  file_out.write(json.dumps(data_out))
  file_out.close()
except:
  print("couldn't open scoreboard/data/achievements.json to write")
  exit(1)