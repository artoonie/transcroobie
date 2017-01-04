from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class HitRequestTest(TestCase):
    def setUp(self):
        User.objects.create_user('user', 'test@testmail.com', 'password')

    def test_login(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('hitrequest:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hitrequest/list.html')

    def test_failed_login(self):
        self.client.login(username='user', password='wrongpass')
        response = self.client.get(reverse('hitrequest:index'))
        self.assertEqual(response.status_code, 302)
