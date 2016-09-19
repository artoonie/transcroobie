from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')
