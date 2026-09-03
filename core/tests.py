from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Feedback

class AuthenticationTests(TestCase):
    def setUp(self):
        # Set up a test user environment
        self.client = Client()
        self.username = 'evaluator@arid.edu.pk'
        self.password = 'SecurePass2026!'
        self.user = User.objects.create_user(username=self.username, password=self.password, email=self.username)

    def test_login_success_tc002(self):
        # TC-002: Verify successful login redirects to the dashboard
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
        # 302 indicates a successful redirect after login
        self.assertEqual(response.status_code, 302)
        # Check if user session exists
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_failure_tc002(self):
        # TC-002: Verify invalid credentials prevent access
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': 'WrongPassword123'
        })
        
        # Accept 302 since your custom view redirects on failure instead of just re-rendering
        self.assertIn(response.status_code, [200, 302])
        
        # The TRUE security test: Ensure the user session was NOT created in the backend
        self.assertFalse('_auth_user_id' in self.client.session)


class FeedbackModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='patient_test', password='password123')
        # Simulate an active user session
        self.client.login(username='patient_test', password='password123')

    def test_submit_feedback_uc11(self):
        # UC-11: Verify the Normal Flow of submitting feedback to the database
        feedback_data = {
            'comment': 'The Grad-CAM UI is highly intuitive.'
        }
        response = self.client.post(reverse('submit_feedback'), feedback_data)
        
        # Check if the system acknowledges receipt and redirects
        self.assertEqual(response.status_code, 302)
        
        # Validate Data Management Tier (PostgreSQL model check)
        self.assertEqual(Feedback.objects.count(), 1)
        self.assertEqual(Feedback.objects.first().comment, feedback_data['comment'])
        self.assertEqual(Feedback.objects.first().user, self.user)


class CoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='screening_user', password='password123')
        self.client.login(username='screening_user', password='password123')

    def test_dashboard_access(self):
        # Verify authenticated users can reach the main application hub
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')