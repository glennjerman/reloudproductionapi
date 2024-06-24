from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings
import os
import binascii
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
class CustomToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='auth_token',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key
    
class CustomTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        model = CustomToken

        UserModel = get_user_model()
        try:
            token = CustomToken.objects.select_related('user').get(key=key)
        except CustomToken.DoesNotExist:
            return None

        if not token.user.is_active:
            return None

        return (token.user, token)
    

class User(AbstractBaseUser):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True,)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Here you can add required fields like first_name, last_name

    def __str__(self):
        return self.email
    
class Audio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    audio = models.FileField(upload_to='audio/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preview_image = models.ImageField(upload_to='audio/preview_image/', null=True, blank=True)

    class Meta:
        unique_together = ('user', 'name')
    
    def __str__(self):
        return self.name
    