from django.contrib import admin

# Register your models here.
from pandemic.models import PlayRoom, Player

admin.site.register(PlayRoom)
admin.site.register(Player)
