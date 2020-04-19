from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from openwisp_notifications.signals import notify
from swapper import load_model

from openwisp_users.tests.utils import TestOrganizationMixin

Notification = load_model('openwisp_notifications', 'Notification')
notification_queryset = Notification.objects.order_by('timestamp')
start_time = timezone.now()
ten_minutes_ago = start_time - timedelta(minutes=10)


class TestNotifications(TestOrganizationMixin, TestCase):
    def setUp(self):
        self.admin = self._create_admin()
        self.notification_options = dict(
            sender=self.admin,
            recipient=self.admin,
            description="Test Notification",
            verb="Test Notification",
            email_subject='Test Email subject',
            url='https://localhost:8000/admin',
        )

    def _create_notification(self):
        notify.send(**self.notification_options)

    def test_superuser_notifications_disabled(self):
        self.assertEqual(self.admin.notificationuser.email, True)
        self.admin.notificationuser.receive = False
        self.admin.notificationuser.save()
        self.assertEqual(self.admin.notificationuser.email, False)
        self._create_notification()
        n = notification_queryset.first()
        self.assertFalse(n.emailed)

    def test_email_sent(self):
        self._create_notification()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.admin.email])
        n = notification_queryset.first()
        self.assertEqual(mail.outbox[0].subject, n.data.get('email_subject'))
        self.assertIn(n.description, mail.outbox[0].body)
        self.assertIn(n.data.get('url'), mail.outbox[0].body)
        self.assertIn('https://', n.data.get('url'))

    def test_email_disabled(self):
        self.admin.notificationuser.email = False
        self.admin.notificationuser.save()
        self._create_notification()
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_not_present(self):
        self.admin.email = ''
        self.admin.save()
        self._create_notification()
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
