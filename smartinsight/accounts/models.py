from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=50)
    subscription_type = models.CharField(max_length=50)