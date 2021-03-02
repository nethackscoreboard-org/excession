from django.db import models

# generic enum property, each enum variant has a name and abbreviatoin
class EnumProp(models.model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)

# game variant - for TNNT this is just vanilla with tnnt mod
class Variant(EnumProp):

# this would be for describing certain mods that aren't quite
# considered variants in themselves
#class Mod(models.Model):

class VariantProp(EnumProp):
    variant = ForeignKey(Variant, on_delete=CASCADE)

# this can use name field as version string
class Version(VariantProp):
    major = models.IntegerField(default=0)
    minor = models.IntegerField(default=0)
    patch = models.IntegerField(default=0)
    #mod =  models.ForeignKey(Mod, on_delete=CASCADE)

class VersionProp(VariantProp):
    version = ForeignKey(Version, on_delete=CASCADE)

class Role(VersionProp):
    allowed_races =  models.ManyToManyField(Race)
    allowed_aligns = models.ManyToManyField(Alignment)

class Race(VersionProp):
    allowed_roles =  models.ManyToManyField(Role)
    allowed_aligns = models.ManyToManyField(Alignment)

class Alignment(VersionProp):

class Gender(VersionProp):

#class Achievement(VersionProp):

#class Conduct(VersionProp):

#class TnntAchieve(VersionProp):
