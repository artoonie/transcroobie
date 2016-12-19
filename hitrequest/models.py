from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

class AudioSnippet(models.Model):
    audio = models.FileField(upload_to='audioparts/%Y-%m-%d')

    # Predictions: each item in the list is a transcription (automatic or AMT)
    predictions = ArrayField(
        models.TextField(blank=True),
        default = []
    )

    # List of incorrectly transcribed words (as determined by AMT)
    # Can't be a multi-d array because it would not be rectangular
    incorrectWords = JSONField( default = {'bools': [] })

    # Has the last prediction been validated?
    activeHITId = models.CharField(max_length=30)

    # Has the last prediction been validated?
    hasBeenValidated = models.BooleanField(default=False)

    # Are we done looking at this HIT? (Potentially given up without validation?)
    isComplete = models.BooleanField(default=False)

class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')

    # list of audio snippets
    audioSnippets = ArrayField(
        models.ForeignKey(AudioSnippet)
    )
    audioSnippets = models.ManyToManyField('hitrequest.AudioSnippet',
                                           related_name='docForSnippet')

    completeTranscript = models.TextField(blank=True)

