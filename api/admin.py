from django.contrib import admin

# Register your models here.
from .models import (
    Profile, Garage, Service, GarageService, PartCategory,
    Part, Review, ForumThread, ForumPost
)

# Use GISModelAdmin for Garage to get a map widget
@admin.register(Garage)
class GarageAdmin(admin.GISModelAdmin):
    list_display = ('name', 'city', 'owner', 'is_verified')
    list_filter = ('is_verified', 'city', 'country')
    search_fields = ('name', 'city', 'owner__username')

admin.site.register(Profile)
admin.site.register(Service)
admin.site.register(GarageService)
admin.site.register(PartCategory)
admin.site.register(Part)
admin.site.register(Review)
admin.site.register(ForumThread)
admin.site.register(ForumPost)