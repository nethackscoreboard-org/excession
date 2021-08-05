conducts = [('food', 'foodless'),
    ('vegn', 'vegan'),
    ('vegt', 'vegetarian'),
    ('athe', 'atheist'),
    ('weap', 'weaponless'),
    ('paci', 'pacifist'),
    ('illi', 'illiterate'),
    ('pile', 'polypileless'),
    ('self', 'polyselfless'),
    ('wish', 'wishless'),
    ('arti', 'artifact wishless'),
    ('geno', 'genocideless'),
    ('elbe', 'elberethless'),
    ('surv', 'survived'),
    ('swap', 'swapchestless'),
    ('neme', 'never killed your quest nemesis'),
    ('vlad', 'never killed Vlad the Impaler'),
    ('wizy', 'never killed the Wizard of Yendor'),
    ('hpom', 'never killed the High Priest of Moloch'),
    ('ride', 'never killed a Rider'),
    ('arts', 'never touched an artifact'),
    ('pets', 'petless'),
    ('deaf', 'permanently deaf'),
    ('hall', 'permanently hallucinated'),
    ('bone', 'bonesless'),
]
template = "- model: scoreboard.conduct\n\
  pk: {}\n\
  fields:\n\
    variant: tnnt\n\
    version: 3.6.6\n\
    short_name: {}\n\
    long_name: {}\n\
    bit_index: {}"

i = 0
for short, long in conducts:
    print(template.format(i + 1, short, long, i))
    i += 1