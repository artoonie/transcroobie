from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField

class AudioSnippet(models.Model):
    audio = models.FileField(upload_to='audioparts/%Y-%m-%d')

    # Predictions: each item in the list is a
    predictions = ArrayField(
         models.TextField(blank=True)
    )

    # Has the last prediction been validated?
    hasBeenValidated = models.BooleanField(default=False)

class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')

    # list of audio snippets
    audioSnippets = ArrayField(
        models.ForeignKey(AudioSnippet)
    )
    audioSnippets = models.ManyToManyField('hitrequest.AudioSnippet',
                                           related_name='docForSnippet')

