#!/bin/bash
# Given a path to the root of the TNNT game source, output YAML to stdout
# containing all of the TNNT achievement names, descriptions, and xlogfile
# fields/bits in a scoreboard-ready format (one that can be passed to manage.py
# loaddata).

if [ -z $1 ]; then
  echo "Usage: script /path/to/tnnt [ > achievements.yaml ]"
  exit 1
fi

if [ ! -e $1 ]; then
  echo That path does not exist.
fi

if [ ! -e ach_to_yaml.awk ]; then
  echo Requires ach_to_yaml.awk to function.
fi

if [ ! -e vanilla_achievements.yaml ]; then
  echo Requires vanilla_achievements.yaml to function.
fi

# vanilla_achievements.yaml is a MANUALLY maintained file of achievements
# present in vanilla (which are expressed in the xlogfile 'achieve' field).
# Since these don't change often, there isn't really a need for automatically
# pulling them from the game.
cat vanilla_achievements.yaml

# Grab the achievements array and chop off the end lines which aren't the
# achievement names
# First line: grab the relevant part of decl.c and chop off the start and end
# lines which aren't actually data values.
# Second line: exclude lines (e.g. comments) which aren't describing achievements.
# Third line: strip C syntax and transform into tab-separated strings.
# Fourth line: apply awk script to turn it into YAML.
sed -n '/tnnt_achievements\[/,/^};$/ p' $1/src/decl.c | head -n -1 | tail -n +2 \
    | sed -e '/^ *[^ {]/ d' \
          -e 's/^ *{//' -e 's/", \?/"\t/' -e 's/\([^\]\)"/\1/g' -e 's/^"//' -e 's/\}.*//' \
    | awk -F'\t' -f ach_to_yaml.awk

# TODO: This does not work on Hardfought.
