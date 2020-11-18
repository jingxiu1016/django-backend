from django.contrib import admin
from english.models import *
# Register your models here.

admin.site.register(User)
admin.site.register(Word)
admin.site.register(Translation)
admin.site.register(DailyLog)
admin.site.register(UserExtension)