from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class PEUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "student_id", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (("Professional Edge", {"fields": ("phone", "country", "role", "student_id")}),)
