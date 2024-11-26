from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import EmailField
from django.db.models import ForeignKey
from django.db.models import ImageField
from django.db.models import SlugField
from django.db.models import TextField
from django.db.models import URLField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for cincoctrl.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

    def has_repo_access(self, repository_id):
        return self.userrole_set.filter(repository__pk=repository_id).exists()

    def has_role(self, repository_id, role):
        return self.userrole_set.filter(
            repository__pk=repository_id,
            role=role,
        ).exists()


class Repository(models.Model):
    ark = CharField(max_length=255, unique=True)
    code = SlugField(unique=True)
    name = CharField(max_length=255)
    description = TextField(blank=True)
    logo = ImageField()
    building = CharField(max_length=255, blank=True)
    address1 = CharField(max_length=255, blank=True)
    address2 = CharField(max_length=255, blank=True)
    city = CharField(max_length=255, blank=True)
    state = CharField(max_length=2, blank=True)
    country = CharField(max_length=2, blank=True)
    zipcode = CharField(max_length=15, blank=True)
    phone = CharField(max_length=15, blank=True)
    contact_email = EmailField(blank=True)
    aeon_url = URLField(blank=True)
    oclc_share = BooleanField(default=False)
    date_created = DateTimeField(auto_now_add=True)
    date_updated = DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_state_line(self):
        return f"{self.city}, {self.state} {self.zipcode}, {self.country}"


class RepositoryLink(models.Model):
    repository = ForeignKey("Repository", on_delete=models.CASCADE)
    url = URLField()
    text = CharField(max_length=255)

    def __str__(self):
        return f"{self.text} ({self.url})"


USER_ROLES = (
    ("local-admin", "Local Admin"),
    ("contributor", "Contributor"),
)


class UserRole(models.Model):
    user = ForeignKey("User", on_delete=models.CASCADE)
    repository = ForeignKey("Repository", on_delete=models.CASCADE)
    role = CharField(max_length=11, choices=USER_ROLES)
    key_contact = BooleanField(default=False)

    def __str__(self):
        return f"{self.repository} / {self.user}"
