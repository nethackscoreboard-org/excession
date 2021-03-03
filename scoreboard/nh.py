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
    def __str__(self):
        return self.name

class Gender(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    def __str__(self):
        return self.name

class Alignment(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    def __str__(self):
        return self.name

class Race(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    #allowed_roles =  models.ManyToManyField(Role)
    allowed_aligns = models.ManyToManyField(Alignment)
    def __str__(self):
        return self.name

class Role(models.Model):
    name    = models.CharField(max_length=100)
    abbrev  = models.CharField(max_length=10)
    version = models.ForeignKey(Version, on_delete=models.CASCADE)
    allowed_races =  models.ManyToManyField(Race)
    allowed_aligns = models.ManyToManyField(Alignment)
    # could also include allowed_genders here but this only
    # applies to valkyrie and I don't really care about gender
    def __str__(self):
        return self.name

#class Achievement(VersionProp):

#class Conduct(VersionProp):

#class TnntAchieve(VersionProp):

# lookup linked fields
def lookup(key, value):
    if key == "version":
        return Version.objects.get(**dict(zip(["major", "minor", "patch"], value.split('.'))))
    elif key == "role":
        return Role.objects.get(abbrev=value)
    elif key == "race":
        return Race.objects.get(abbrev=value)
    elif key in ["align", "align0"]:
        return Alignment.objects.get(abbrev=value)
    elif key in ["gender", "gender0"]:
        return Gender.objects.get(abbrev=value)
