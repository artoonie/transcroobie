import mock
import os
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile

from hitrequest.models import Document
from transcroobie import settings

testFilepath = 'dRetroist-201-Xanadu_cropped.mp3'

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
            expectedRelpath = fp.name
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

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('hitrequest.views._processUploadedDocument.delay')
    def test_hit_submission(self, delay):
        self.login()
        self.uploadAudio()

        self.assertTrue(delay.called)

        # GET data
        audioFile = Document.objects.latest('docfile')
        docId = audioFile.id
        self.assertEqual(docId, 1)
        assignmentId = "ASSIGNMENT_ID_NOT_AVAILABLE"
        hitId = "3HEA4ZVWVCLIGVGE95R5FB2KOCC55X"
        getData = {'assignmentId': assignmentId, 'docId': docId, 'hitId': hitId}

        response = self.client.get(reverse('fixHIT'), getData)
        self.assertEqual(response.status_code, 200)
