from django.contrib import admin

# Register your models here.
from .nh import Variant, Version, Gender, Alignment, Race, Role
from .models import LogSource

admin.site.register(LogSource)
admin.site.register(Variant)
admin.site.register(Version)
admin.site.register(Gender)
admin.site.register(Alignment)
admin.site.register(Race)
admin.site.register(Role)