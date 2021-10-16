from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from scoreboard.models import Player
from .settings import DGL_DATABASE_PATH
import sqlite3
import crypt

def get_dgl_cursor():
    # open in read-only mode
    dgl_conn = sqlite3.connect('file:' + DGL_DATABASE_PATH + '?mode=ro', uri=True)
    dgl_conn.row_factory = sqlite3.Row
    return dgl_conn.cursor()

# Function that looks up a player in first the Player table, then if not found
# there then in dgamelaunch database. If found in dgamelaunch, create the player
# in the Player table and return
def find_player(findname):
    try:
        return Player.objects.get(name=findname)
    except Player.DoesNotExist as e:
        try:
            dgl_curs = get_dgl_cursor()
            uname = dgl_curs.execute('SELECT username FROM dglusers WHERE username = ?',
                                     (findname,)).fetchone()
        except sqlite3.Error as e:
            print('ERROR connecting to or executing SQL on sqlite database')
            print('  db path:', DGL_DATABASE_PATH)
            print('  username:', username)
        if uname is None:
            # not found in dgl, doesn't apparently exist
            raise e
        else:
            player = Player(name=findname, clan=None, clan_admin=False)
            player.save()
            return player

class HdfAuthBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None):
        try:
            dgl_curs = get_dgl_cursor()
            # get hashed salted password from dgl
            pwd_hash = dgl_curs.execute('SELECT password FROM dglusers WHERE username = ?', (username,)).fetchone()
        except sqlite3.Error as e:
            print('ERROR connecting to or executing SQL on sqlite database')
            print('  db path:', DGL_DATABASE_PATH)
            print('  username:', username)
            return None
        print(pwd_hash)
        if pwd_hash is None:
            # doesn't exist in dgl, can't join site
            return None
        else:
            # convert from tuple containing 1 string to just the string
            pwd_hash = pwd_hash[0]
        # compare it against submitted password with crypt
        if crypt.crypt(password, pwd_hash) != pwd_hash:
            print('failed login attempt by', username)
            return None

        # success! this is the correct dgl password. look up the user or create
        # if doesn't exist (TNNT login and registration are one and the same)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            player = find_player(username)
            # link to the User record
            player.user = user
            player.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
