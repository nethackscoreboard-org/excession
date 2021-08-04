from django.test import TestCase
from scoreboard.parsers import XlogParser

sample_xlog = {
    'name': 'asdf',
    'version': '3.6.6',
    'death': 'killed by a Fox',
}

def gen_xlog(modifier):
    xlog_copy = sample_xlog.copy()
    xlog_copy['death'] = xlog_copy['death'] + modifier
    return "\t".join([ '='.join([k, v]) for k, v in xlog_copy.items() ])

class XlogParserTest(TestCase):
    def setUp(self):
        self.parser = XlogParser()
        pass

    def test_missing_required_fields(self):
        self.assertRaises(ValueError, self.parser.createGameRecord, "death=ascended\thp=24")
        pass

    def test_malformed_input(self):
        self.assertRaises(ValueError, self.parser.createGameRecord, "foobar")
        self.assertRaises(ValueError, self.parser.createGameRecord, "foo=bar")
        pass

    def test_control_chars_in_input(self):
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\n"))
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\r"))
        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\0"))
        pass

#    def test_invalid_utf8_in_input(self):
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xc3\x28"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xa0\xa1"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xe2\x28\xa1"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xe2\x82\x28"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xf0\x28\x8c\xbc"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xf0\x90\x28\xbc"))
#        self.assertRaises(ValueError, self.parser.createGameRecord, gen_xlog("\xf0\x28\x8c\x28"))
#        pass
    
