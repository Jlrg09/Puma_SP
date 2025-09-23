from django.contrib import admin
from .models import Office


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
	list_display = ('name', 'supervisor')
	search_fields = ('name',)

# Register your models here.
