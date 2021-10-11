from django.core.management.base import BaseCommand, CommandError
from scoreboard.models import Source, Game, GameManager
from scoreboard.parsers import XlogParser
import urllib

class Command(BaseCommand):
    help = 'Poll Sources (xlogfiles) for new game data'

    def handle(self, *args, **options):
        for src in Source.objects.all():
            print('polling source: ' + src.server)

            # TODO: save fpos and only fetch latest data, also save local copy of xlog file
            http_stream = urllib.request.urlopen(src.location)
            raw_dict_array = XlogParser().parse(http_stream)
            for xlog_dict in raw_dict_array:
                game = Game.objects.from_xlog(src, xlog_dict)

        self.stdout.write('listed sources')