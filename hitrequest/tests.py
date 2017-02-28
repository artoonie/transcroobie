import json
import mock
import os
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile

from hitrequest.models import AudioSnippet, Document
from transcroobie import settings

testFilepath = 'testData/retroist-cropped-again.wav'

class HitRequestTest(TestCase):
    def setUp(self):
        settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
        settings.MEDIA_ROOT = tempfile.mkdtemp()

        docfileField = Document._meta.get_field('docfile')
        docfileField.storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        docfileField.upload_to = 'documents/'

        User.objects.create_user('user', 'test@testmail.com', 'password')

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)

    def login(self):
        self.client.login(username='user', password='password')

    def uploadAudio(self):
        assert os.path.exists(testFilepath)
        with file(testFilepath) as fp:
            response = self.client.post(reverse('hitrequest:index'),
                    {'uploadedFile': fp}, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_model_save(self):
        """ Ensures the file storage is connected and saving to the correct
            MEDIA_ROOT location """
        with file(testFilepath) as fp:
            newFile = SimpleUploadedFile(fp.name, fp.read())
            newDoc = Document(docfile = newFile)
            newDoc.save()
            expectedRelpath = os.path.basename(fp.name)
            self.assertEqual(newFile.name, expectedRelpath)
        expectedFullpath = os.path.join(settings.MEDIA_ROOT, 'documents', expectedRelpath)
        assert os.path.exists(expectedFullpath)

    def test_upload_audio(self):
        self.login()
        self.uploadAudio()

    def test_login(self):
        self.login()
        response = self.client.get(reverse('hitrequest:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hitrequest/list.html')

    def test_failed_login(self):
        self.client.login(username='user', password='wrongpass')
        response = self.client.get(reverse('hitrequest:index'))
        self.assertEqual(response.status_code, 302)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @mock.patch('googleapiclient.http.HttpRequest.execute')
    def test_hit_submission(self, mockExecute):
        """ This is the primary integration test: a roundtrip check/fix """
        def googleSpeechExecute(self):
            data = json.loads(self.body)
            expectedStart = 'gs://transcroobie-clips/audioparts'
            assert data['audio']['uri'].startswith(expectedStart)
            return {u'results':
                [{u'alternatives': [{u'confidence': 0.73709655, u'transcript':
                u"I grew up in the house with two older siblings wonderful "\
                "people, but when you're the youngest sibling, I maybe this is "\
                "not a problem today screens are everywhere when you were "\
                "younger sibling back when you"}]}]}
        mockExecute.side_effect = googleSpeechExecute

        self.login()
        self.uploadAudio()

        # GET data
        assignmentId = "ASSIGNMENT_ID_NOT_AVAILABLE"
        hitId = "3HEA4ZVWVCLIGVGE95R5FB2KOCC55X"
        audioSnippet = AudioSnippet.objects.latest('audio')
        getData = {'assignmentId': assignmentId,
                   'docId': audioSnippet.id,
                   'hitId': hitId}

        response = self.client.get(reverse('checkHIT'), getData)
        self.assertEqual(response.status_code, 200)

        # POST data
        response = self.client.get(reverse('checkHIT'), getData)
