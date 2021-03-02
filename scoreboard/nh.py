from django.db import models

# generic enum property, each enum variant has a name and abbreviatoin
class EnumProp(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)

# game variant - for TNNT this is just vanilla with tnnt mod
class Variant(EnumProp):
    __foo__ = 1

# this would be for describing certain mods that aren't quite
# considered variants in themselves
#class Mod(models.Model):

class VariantProp(EnumProp):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)

# this can use name field as version string
class Version(VariantProp):
    major = models.IntegerField(default=0)
    minor = models.IntegerField(default=0)
    patch = models.IntegerField(default=0)
    #mod =  models.ForeignKey(Mod, on_delete=models.CASCADE)

class VersionProp(VariantProp):
    version = models.ForeignKey(Version, on_delete=models.CASCADE)

class Gender(VersionProp):
    __foo__ = 1

class Alignment(VersionProp):
    __foo__ = 1

class Race(VersionProp):
    #allowed_roles =  models.ManyToManyField(Role)
    allowed_aligns = models.ManyToManyField(Alignment)

class Role(VersionProp):
    allowed_races =  models.ManyToManyField(Race)
    allowed_aligns = models.ManyToManyField(Alignment)

#class Achievement(VersionProp):

#class Conduct(VersionProp):

#class TnntAchieve(VersionProp):
