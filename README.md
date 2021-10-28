# TNNT backend powered by Django REST Framework
This is a rewrite of the old
[Perl backend](https://github.com/tnnt-devteam/tnnt-backend), intended to be
designed as a REST API using
[Django REST framework](https://www.django-rest-framework.org/). Game data is
source from xlogfile entries and stored in a database using
[Django](https://www.djangoproject.com/)'s
[object model](https://docs.djangoproject.com/en/3.2/topics/db/models/) as DB
abstraction.
[Django REST Serializers](https://www.django-rest-framework.org/api-guide/serializers/)
provide an abstraction for deserializing xlogfile data and serializing query
results before rendering the output as JSON.

## Endpoints
 - `/` - returns dictionary of the form {endpoint}: {endpoint url}
 - `/games` - all games
 - `/ascended` - all ascensions
 - `/players` - list of players
 - `/players/<name>` - games by player <name>
 - `/players/<name>` - ascensions by player <name>
 - `/leaderboards` - list of leaderboards
 - `/leaderboards/conducts`
 - `/leaderboards/minscore`
 - `/leaderboards/realtime`
 - `/leaderboards/turncount`
 - `/leaderboards/wallclock`

## Dependencies and setup

### Arch Linux
```shell
$ sudo pacman -S mariadb mariadb-clients python-mysqlclient python-yaml
$ sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
$ sudo systemctl start mysql.service
```

### Debian/Ubuntu
```shell
$ sudo apt-get install python3 pip mariadb-server mariadb-client
$ sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
```

### macOS Big Sur
In order for the rest of this guide to be consistent, add the following to `~/.zshrc`.
```shell
alias python='python3'
alias pip='pip3'
```
Install mariadb:
```shell
$ brew install mariadb
$ mysql.server start
```

### OS-independent steps
#### Optional: enter python virtual environment before installing dependencies
```shell
$ virtualenv env --no-site-packages
$ source env/bin/activate
```

### Install python dependencies
`$ pip install -r requirements.txt`

### Create secrets file
Go to http://www.miniwebtool.com/django-secret-key-generator/ and add add the
following to secrets.sh:
```shell
export SECRET_KEY='<your_key_here>'
export DATABASE_PASSWORD='<db_pass_here>'
```
`$ source secrets.sh`

### Setup database
`$ sudo mysql`
```sql
> CREATE DATABASE scoreboard;
> CREATE USER 'tnnt'@'localhost' IDENTIFIED BY '<db_pass_here>';
> GRANT ALL ON *.* TO 'tnnt'@'localhost';
```
#### migrate
```shell
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py makemigrations scoreboard
$ python manage.py migrate
```

#### Import achievements, conducts, and trophies data
Note: this requires a copy of the TNNT game source to pull TNNT achievement
names and descriptions from. However, achievements are now part of the repository,
and the first command below only needs to be run if/when achievements are modified
in the TNNT game source code. The import of fixtures should also only be done once,
when a fresh Django server is being set up.
```shell
$ ./ach_to_yaml.sh /path/to/tnnt/source > scoreboard/fixtures/achievements.yaml
$ python manage.py loaddata achievements conducts sources trophies
```

### Running and operation
The pollxlogs command will read xlog data from a list of sources with associated URLs,
saved in the DB. Those sources were defined as fixtures and imported with the above
loaddata command. The aggregate command will loop over all games and compute various
aggregate data for individual players and for clans standings.
```shell
$ ./manage.py pollxlogs
$ ./manage.py aggregate
```

#### Optional: point DGL\_DATABASE\_PATH at real database
This is in `tnnt/settings.py`. By default, it points at `dgamelaunch_test.db`,
which provides several "registered dgamelaunch accounts" (alice, bob, chuck,
david, eve, fred, and gimli; each password is the same as the username) for
dev and testing purposes. For production, you will want to point this to the
full path of the real dgamelaunch sqlite database.

### Run dev server
`$ python manage.py runserver`
