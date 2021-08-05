from django.test import TestCase
from scoreboard.parsers import XlogParser
from scoreboard.models import Achievement, Conduct, GameRecord
from scripts.achievements import load_achievements
from datetime import datetime, timedelta, timezone

sample_xlog = {
    'name': 'asdf',
    'version': '3.6.6',
    'death': 'killed by a Fox',
    'role': 'Valkyrie',
    'starttime': '1604188860',
    'endtime': '1604188935',
    'turns': '165',
    'achieve': '0x0',
}
sample_xlog_line = "version=3.6.6	points=87	deathdnum=0	deathlev=1	maxlvl=2	\
    hp=0	maxhp=12	deaths=1	deathdate=20201101	birthdate=20201101	uid=5	role=Hea	race=Gno	\
gender=Mal	align=Neu	name=thorsb	death=killed by a water demon	conduct=0x11fdfcf	turns=165	\
achieve=0x0	realtime=74	starttime=1604188860	endtime=1604188935	gender0=Mal	align0=Neu	flags=0x4	\
tnntachieve0=0x0	tnntachieve1=0x0	tnntachieve2=0x0	tnntachieve3=0x0"
sample_server = 'hdf-us'
sample_conducts = [
    ['asdf', 'fake conduct'],
    ['zomg', 'zomg lol yay'],
    ['lols', 'idk what im doin'],
    ['heya', 'asdf fjsladjfj'],
    ['fooo', 'peopel are uman'],
    ['moma', 'moma dont love me'],
    ['babe', 'baby wanna cracker'],
    ['geno', 'genocide route'],
    ['valk', 'valkyrie love'],
]
sample_ach_conducts = [
    ['zen', 'you know, blind'],
    ['nude', 'streaker wooooo'],
]

def gen_xlog(modifiers):
    xlog_copy = sample_xlog.copy()
    for key in modifiers:
        xlog_copy[key] = modifiers[key]
    return "\t".join([ '='.join([k, v]) for k, v in xlog_copy.items() ])

class XlogParserTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i, conduct in enumerate(sample_conducts):
            Conduct.objects.create(variant='tnnt', version='3.6.6', short_name=conduct[0], long_name=conduct[1], bit_index=i)
        for i, achieve in enumerate(sample_ach_conducts):
            Conduct.objects.create(variant='tnnt', version='3.6.6', short_name=achieve[0], long_name=achieve[1], bit_index=i, achieve_field=True)
        load_achievements()

    def setUp(self):
        self.parser = XlogParser(sample_server)
        pass

    def test_missing_required_fields(self):
        self.assertRaises(ValueError, self.parser.createGameRecord, "death=ascended\thp=24")
        pass

    def test_malformed_input(self):
        self.assertRaises(ValueError, self.parser.createGameRecord, "foobar")
        self.assertRaises(ValueError, self.parser.createGameRecord, "foo=bar")
        pass

    def test_control_chars_in_input(self):
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog({'death': "\n"}))
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog({'death': "\r"}))
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog({'death': "\0"}))
        pass

    def test_valid_xlog_record(self):
        game_record = self.parser.createGameRecord(gen_xlog({}))
        self.assertEqual(game_record.won, False)
        self.assertEqual(game_record.name, sample_xlog['name'])
        game_record = self.parser.createGameRecord(sample_xlog_line)
        self.assertEqual(game_record.align, 'Neu')
        self.assertEqual(game_record.realtime, timedelta(seconds=74))
        pass
    
    def test_starttime_after_endtime(self):
        starttime = datetime.now().timestamp()
        endtime = datetime.now() - timedelta(days=5)
        params = {'starttime': f"{starttime}", 'endtime': f"{endtime}"}
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog(params))
        pass

    def test_realtime_greater_than_wallclock(self):
        realtime = '40000'
        starttime = datetime.now().timestamp()
        endtime = datetime.now() - timedelta(seconds=5)
        params = {'starttime': f"{starttime}", 'endtime': f"{endtime}", 'realtime': f"{realtime}"}
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog(params))
        pass
    
    def test_xlog_server_overrides_parser_server(self):
        params = {'server': 'hdf-eu'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.server, 'hdf-eu')
        pass

    def test_future_times(self):
        starttime = int((datetime.now() + timedelta(days=1)).timestamp())
        endtime = int((datetime.now() + timedelta(days=3)).timestamp())
        realtime = int(timedelta(days=1).total_seconds())
        params = {'starttime': f"{starttime}", 'endtime': f"{endtime}", 'realtime': f"{realtime}"}
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog(params))
        starttime = int((datetime.now() - timedelta(days=1)).timestamp())
        endtime = int((datetime.now() + timedelta(days=1)).timestamp())
        realtime = int(timedelta(days=1).total_seconds())
        params = {'starttime': f"{starttime}", 'endtime': f"{endtime}", 'realtime': f"{realtime}"}
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog(params))
        pass

    def test_flags(self):
        params = {'flags': '0x4'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.bonesless, True)
        params = {'flags': '0x6'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.explore, True)
        self.assertEqual(game_record.bonesless, True)
        params = {'flags': '0x1'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.wizmode, True)
        pass

    def test_conducts(self):
        params = {'conduct': '0x8'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertIsNotNone(game_record.conducts.filter(short_name='heya'))
        params = {'conduct': '0x9'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertIsNotNone(game_record.conducts.filter(short_name='heya'))
        self.assertIsNotNone(game_record.conducts.filter(short_name='asdf'))
        params = {'conduct': '0x6'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.conducts.filter(short_name='asdf').count(), 0)
        self.assertEqual(game_record.conducts.filter(short_name='heya').count(), 0)
        self.assertIsNotNone(game_record.conducts.filter(short_name='zomg'))
        self.assertIsNotNone(game_record.conducts.filter(short_name='lols'))
        self.assertEqual(GameRecord.objects.filter(conducts__short_name='asdf').count(), 1)
        self.assertEqual(GameRecord.objects.filter(conducts__short_name='heya').count(), 2)
        self.assertEqual(GameRecord.objects.filter(conducts__short_name='zomg').count(), 1)
        self.assertEqual(GameRecord.objects.filter(conducts__short_name='lols').count(), 1)
        self.assertEqual(GameRecord.objects.filter(conducts__short_name='geno').count(), 0)
        params = {'achieve': '0x2'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(GameRecord.objects.filter(conducts__short_name='nude').count(), 1)
        pass

    def test_achievements(self):
        params = {'achieve': '0x2', 'tnntachieve0': '0x80', 'tnntachieve1': '0x9c', 'tnntachieve2': '0x40', 'tnntachieve3': '0x6'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.achievements.all().count(), 9)
        self.assertIsNotNone(game_record.achievements.filter(title='Feel the Burn'))
        self.assertIsNotNone(game_record.achievements.filter(title='More Light'))
        self.assertIsNotNone(game_record.achievements.filter(title='Captain Ahab'))
        self.assertIsNotNone(game_record.achievements.filter(title='Indulgences'))
        self.assertIsNotNone(game_record.achievements.filter(title='The Archetypal Hero'))
        self.assertIsNotNone(game_record.achievements.filter(title='Musical Mastermind'))
        self.assertIsNotNone(game_record.achievements.filter(title='Tainted'))
        self.assertIsNotNone(game_record.achievements.filter(title='The Deathly Hallows'))
        self.assertIsNotNone(game_record.achievements.filter(title='Indiana Jones'))
    
    def test_won(self):
        params =  {'achieve': '0x100'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.won, True)
        params =  {'death': 'ascended'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.won, True)
        params =  {'death': 'foobar', 'achieve': '0x00'}
        game_record = self.parser.createGameRecord(gen_xlog(params))
        self.assertEqual(game_record.won, False)

#    def test_invalid_utf8_in_input(self):
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xc3\x28"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xa0\xa1"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xe2\x28\xa1"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xe2\x82\x28"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xf0\x28\x8c\xbc"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xf0\x90\x28\xbc"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xf0\x28\x8c\x28"))
#        pass
    
