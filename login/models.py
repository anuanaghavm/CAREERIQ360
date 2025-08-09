import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, phone_number, section, country, city, dob, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            phone_number=phone_number,
            section=section,
            country=country,
            city=city,
            dob=dob,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone_number, section, country,city, dob, password):
        user = self.create_user(email, name, phone_number, section, country, city, dob, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    SECTION_CHOICES = [
        ("Ages 13-15", "Ages 13-15"),
        ("Ages 16-18", "Ages 16-18"),
        ("UG/PG", "UG/PG"),
        ("Professional", "Professional"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=300)
    dob = models.DateField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone_number', 'section', 'country', 'city','dob']

    def __str__(self):
        return self.email
