from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    objects = UserManager()


class Link(models.Model):
    TYPE_CHOICES = [
        ('website', 'Website'),
        ('book', 'Book'),
        ('article', 'Article'),
        ('music', 'Music'),
        ('video', 'Video'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(unique=True)
    image = models.URLField(blank=True, null=True)
    link_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='website')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    links = models.ManyToManyField(Link, related_name='collections', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)