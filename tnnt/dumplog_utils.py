# TODO: Once Game no longer depends on this function, move it out of its own
# file (to hardfought_utils perhaps). It's only in here right now because of
# circular import errors.

# Given a dumplog format, player name, and datetime object representing the
# start time of one of that player's games, return a valid dumplog URL.
def format_dumplog(fmt, playername, starttime):
    return fmt.replace('%n1', playername[0]) \
              .replace('%n', playername) \
              .replace('%st', str(int(starttime.timestamp())))
