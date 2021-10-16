# TNNT backend powerd by Django REST Framework
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
### Ubuntu/Debian
```shell
$ sudo apt-get install python3 pip mariadb-server mariadb-client
$ sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
```

### Arch Linux
```shell
$ sudo pacman -S mariadb mariadb-clients python-mysqlclient python-yaml
$ sudo mysql_install_db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
$ sudo systemctl start mysql.service
```

#### Optional: enter python virtual environment before install deps
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
> CREATE USER tnnt IDENTIFIED BY '<db_pass_here>';
> GRANT ALL ON *.* TO tnnt;
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
names and descriptions from.
```shell
$ ./ach_to_yaml.sh /path/to/tnnt/source > scoreboard/fixtures/achievements.yaml
$ python manage.py loaddata achievements conducts trophies
```

#### Optional: import test data from xlogfile (e.g. `tnnt-2020-eu`)
`$ python manage.py shell`
```python
>>> from scripts.test_data import TestData
>>> TestData().import_and_save_from_xlogfile('tnnt-2020-eu')
```

#### Optional: point DGL\_DATABASE\_PATH at real database
This is in `tnnt/settings.py`. By default, it points at `dgamelaunch_test.db`,
which provides several "registered dgamelaunch accounts" (alice, bob, chuck,
david, eve, fred, and gimli; each password is the same as the username) for
dev and testing purposes. For production, you will want to point this to the
full path of the real dgamelaunch sqlite database.

### Run dev server
`$ python manage.py runserver`
