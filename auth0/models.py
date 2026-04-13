from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager

# Create your models here.
class CustomUserManager(BaseUserManager):
    """
    Defines how the User(or the model to which attached)
    will create users and superusers.
    """
    def create_user(self,email,password, **extra_fields):
        """
        Create and save a user with the given email, password
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        if not password:
            raise ValueError("Password must be provided")

        email = self.normalize_email(email) # lowercase the domain
        user = self.model(email=email,**extra_fields)
        user.set_password(password) # hash raw password and set
        user.save()
        return user
    def create_superuser(self,email, password,**extra_fields):
        """
        Create and save a superuser with the given email, 
        password, and date_of_birth. Extra fields are added
        to indicate that the user is staff, active, and indeed
        a superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                _("Superuser must have is_staff=True.")
            )
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                _("Superuser must have is_superuser=True.")
            )
        return self.create_user(email, password, **extra_fields)
class CustomUser(AbstractUser):
    """
    Custom user model which doesn't have a username, 
    but has a unique email and a reg date. 
    This model is used for both superusers and 
    regular users as well.
    """
    # The inherited field 'username' is nullified, so it will 
    # neither become a DB column nor will it be required.
    username = None
    email = models.EmailField(_("email address"), unique=True)
    userId = models.CharField(max_length=100, unique=True, null=False, blank=False)
    token = models.CharField(max_length=500,null=False, blank=False)
    account_created_on = models.DateField(
        verbose_name="account_created_on",
        null=True
    )
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=30)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    # Set up the email field as the unique identifier for users.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]

    objects = CustomUserManager()
    def __str__(self):
        return self.email


