# dependencies and setup

install python3 and pip

#### optional: enter python virtual environment before install deps
`$ virtualenv env --no-site-packages`
source env/bin/activate

### install python dependencies
`$ pip install -r requirements.txt`

### setup secrets
go to http://www.miniwebtool.com/django-secret-key-generator/
add the following to secrets.sh
```shell
export SECRET_KEY='<your_key_here>'
```
`$ source secrets.sh`

### setup database
```shell
$ python manage.py migrate
$ python manage.py createsuperuser
$ python manage.py makemigrations scoreboard
$ python manage.py migrate
```

### run dev server
`$ python manage.py runserver`
