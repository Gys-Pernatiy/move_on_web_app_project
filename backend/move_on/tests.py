from django.test import TestCase
from .models import User, Walk


class WalkAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            telegram_id=123456789,
            username="test_user",
            energy=100
        )

    def test_start_walk(self):
        response = self.client.post('/walk/start/', {
            'telegram_id': self.user.telegram_id
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('walk_id', response.json())
