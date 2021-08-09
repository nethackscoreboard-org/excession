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

## Dependencies and setup
Install python3 and pip

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
```
`$ source secrets.sh`

### Setup database
```shell
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py makemigrations scoreboard
$ python manage.py migrate
```

#### Optional: import test data from xlogfile (e.g. `tnnt-2020-eu`)
`$ python manage.py shell`
```python
>>> from scripts.test_data import TestData
>>> TestData().import_and_save_from_xlogfile('tnnt-2020-eu')
```

### Run dev server
`$ python manage.py runserver`
