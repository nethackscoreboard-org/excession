import json
import math
template = "- model: scoreboard.achievement\n\
  pk: {}\n\
  fields:\n\
    variant: tnnt\n\
    version: 3.6.6\n\
    title: {}\n\
    description: {}\n\
    xlog_field: {}\n\
    bit_index: {}"

data = open('tnnt_achievements.json',)
data = json.load(data)
i = 1
for value in data.values():
  xlog_field = [k for k in value.keys()][0]
  bit_index = int(math.log(int(value[xlog_field], 0), 2))
  print(template.format(i, value['title'], value['descr'], xlog_field, bit_index))
  i += 1
