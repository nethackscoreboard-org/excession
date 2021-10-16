#!/bin/bash

. secrets.sh
./manage.py migrate scoreboard zero && rm -r scoreboard/migrations/* && \
    ./manage.py makemigrations scoreboard && ./manage.py migrate scoreboard
