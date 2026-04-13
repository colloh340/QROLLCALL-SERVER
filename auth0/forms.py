from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Specify the user model created while adding a user
    on the admin page.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "account_created_on",
            "image_url",
            "userId",
            "is_staff",
            "is_active",
            "groups",
            "user_permissions"
        ]


class CustomUserChangeForm(UserChangeForm):
    """
    Specify the user model edited while editing a user on the
    admin page.
    """
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "account_created_on",
            "is_staff",
            "is_active",
            "groups",
            "user_permissions"
        ]
