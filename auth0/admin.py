from django.contrib import admin
from . models import CustomUser
from django.contrib.auth.admin import UserAdmin
from . forms import CustomUserChangeForm, CustomUserCreationForm

# Register your models here.
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = (
        "email",
        "first_name",
        "last_name",
        "account_created_on",
        "is_staff",
        "is_active",
        "userId",
    )
    list_filter = (
        "email",
        "first_name",
        "last_name",
        "account_created_on",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": (
            "first_name",
            "last_name", 
            "email", 
            "password",
            "userId",
            "token",
            "image_url",
            "account_created_on")}
        ),
        ("Permissions", {"fields": (
            "is_staff", 
            "is_active", 
            "groups", 
            "user_permissions")}
        ),
    )
    add_fieldsets = (
        ( None, {"fields": (
            "first_name",
            "last_name",
            "email",
            "userId",
            "token",
            "image_url",
            "password1",
            "password2",
            "account_created_on",
            "is_staff",
            "is_active",
            "groups",
            "user_permissions")}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)
    
admin.site.register(CustomUser, CustomUserAdmin)