from background_task import background
from .models import LogSource

@background(schedule=60)
def process_sources():
    for source in LogSource.objects.all():
        # download from source.location if not null,
        # seek to source.file_pos
        # backup to source.local_file
        # process new lines with parser