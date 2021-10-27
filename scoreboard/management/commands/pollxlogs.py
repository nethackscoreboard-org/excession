from django.core.management.base import BaseCommand
from scoreboard.models import Source, Game
from django.db import transaction
from scoreboard.parsers import XlogParser
from tnnt.settings import XLOG_DIR
from pathlib import Path
import requests


@transaction.atomic
def import_records(src):
    xlog_path = Path(XLOG_DIR) / src.local_file
    with xlog_path.open("r") as xlog_file:
        xlog_file.seek(src.file_pos)
        for xlog_entry in XlogParser().parse(xlog_file):
            Game.objects.from_xlog(src, xlog_entry).save()
        src.file_pos = xlog_file.tell()
        src.save()


def sync_local_file(url, local_file):
    xlog_path = Path(XLOG_DIR) / local_file
    with xlog_path.open("ab") as xlog_file:
        r = requests.get(url, headers={"Range": f"bytes={xlog_file.tell()}-"})
        # 206 means they are honouring our Range request c:
        if r.status_code != 206:
            return
        for chunk in r.iter_content(chunk_size=128):
            xlog_file.write(chunk)


class Command(BaseCommand):
    help = "Poll Sources (xlogfiles) for new game data"

    def handle(self, *args, **options):
        sources = Source.objects.all()
        if len(sources) == 0:
            raise RuntimeError('There are no sources in the database to poll!')
        for src in sources:
            sync_local_file(src.location, src.local_file)
            import_records(src)
