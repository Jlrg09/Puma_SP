from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


class RegistrationApprovalTests(TestCase):
    def test_unapproved_user_redirected_to_waiting(self):
        u = User.objects.create_user(username='u1', password='pass12345', approved=False)
        self.client.login(username='u1', password='pass12345')
        resp = self.client.get('/')
        self.assertRedirects(resp, reverse('waiting'), fetch_redirect_response=False)

    def test_approved_user_can_access_home(self):
        u = User.objects.create_user(username='u2', password='pass12345', approved=True)
        self.client.login(username='u2', password='pass12345')
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

# Create your tests here.
