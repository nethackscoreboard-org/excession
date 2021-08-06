import json
conducts = [('food', 'foodless'),
    ('vegn', 'vegan'),
    ('vegt', 'vegetarian'),
    ('athe', 'atheist'),
    ('weap', 'weaponless'),
    ('paci', 'pacifist'),
    ('illi', 'illiterate'),
    ('pile', 'polyless'),
    ('self', 'polyselfless'),
    ('wish', 'wishless'),
    ('arti', 'artiwishless'),
    ('geno', 'genocideless'),
    ('elbe', 'elberethless'),
    ('surv', 'never_died'),
    ('swap', 'never_used_the_swap_chest'),
    ('neme', 'never_killed_quest_nemesis'),
    ('vlad', 'never_killed_vlad'),
    ('wizy', 'never_killed_rodney'),
    ('hpom', 'never_killed_the_high_priest_of_moloch'),
    ('ride', 'never_killed_a_rider'),
    ('arts', 'never_touched_an_artifact'),
    ('pets', 'petless'),
    ('deaf', 'deaf'),
    ('hall', 'hallucinating'),
    ('bone', 'bonesless'),
]

def save_conducts():
  data = {
    hex(1<<i): {conduct[0]: conduct[1]}
    for i, conduct in enumerate(conducts)
  }
  achieve_conducts = {
    hex(4096): {'zen': 'blind'},
    hex(8192): {'nude': 'nudist'}
  }
  serialized = json.dumps({'conduct': data, 'achieve': achieve_conducts})
  try:
    file = open('scoreboard/data/conducts.json', 'w')
    file.write(serialized)
    file.close()
  except:
    print("could not open scoreboard/data/conducts.json for writing")

save_conducts()