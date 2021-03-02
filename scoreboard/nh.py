from django.db import models

## generic enum property, each enum variant has a name and abbreviatoin
# if i try to do this I get errors about fields in the extented classes
# clashing with fields in the generic class (that shouldn't exist)
##class EnumProp(models.Model):

# game variant - for TNNT this is just vanilla with tnnt mod
class Variant(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)

# this would be for describing certain mods that aren't quite
# considered variants in themselves
#class Mod(models.Model):

# this can use name field as version string
class Version(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    major = models.IntegerField(default=0)
    minor = models.IntegerField(default=0)
    patch = models.IntegerField(default=0)
    #mod =  models.ForeignKey(Mod, on_delete=models.CASCADE)

class Gender(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)

class Alignment(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)

class Race(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    #allowed_roles =  models.ManyToManyField(Role)
    allowed_aligns = models.ManyToManyField(Alignment)

class Role(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    allowed_races =  models.ManyToManyField(Race)
    allowed_aligns = models.ManyToManyField(Alignment)

#class Achievement(VersionProp):

#class Conduct(VersionProp):

#class TnntAchieve(VersionProp):
