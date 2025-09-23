from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
	model = CustomUser
	list_display = ('username', 'first_name', 'last_name', 'email', 'id_type', 'id_number', 'birth_date', 'approved', 'role', 'office', 'is_active', 'is_staff')
	list_filter = ('approved', 'role', 'is_active', 'is_staff', 'office', 'id_type')
	fieldsets = UserAdmin.fieldsets + (
		('Gestor de Servicios', {'fields': ('approved', 'role', 'office', 'id_type', 'id_number', 'birth_date', 'phone')}),
	)
	add_fieldsets = UserAdmin.add_fieldsets + (
		('Gestor de Servicios', {'fields': ('approved', 'role', 'office', 'id_type', 'id_number', 'birth_date', 'phone')}),
	)

# Register your models here.
