from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from api.models import CallRecord, Contact, ContactList


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.contact = Contact.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            city="Test City",
            phone_number="+1234567890",
        )
        self.contact_list = ContactList.objects.create(user=self.user, name="Test List")
        self.contact_list.contacts.add(self.contact)
        self.call_record = CallRecord.objects.create(
            sid="TEST123",
            user=self.user,
            contact=self.contact,
            phone_number="+1234567890",
            duration=60,
            cost=Decimal("1.50"),
            status="completed",
        )

    def test_contact_creation(self):
        self.assertEqual(self.contact.first_name, "John")
        self.assertEqual(self.contact.last_name, "Doe")
        self.assertEqual(self.contact.city, "Test City")
        self.assertEqual(self.contact.phone_number, "+1234567890")
        self.assertEqual(self.contact.user, self.user)
        self.assertEqual(str(self.contact), "John Doe")

    def test_contact_list_creation(self):
        self.assertEqual(self.contact_list.name, "Test List")
        self.assertEqual(self.contact_list.user, self.user)
        self.assertIn(self.contact, self.contact_list.contacts.all())
        self.assertEqual(str(self.contact_list), "Test List")

    def test_call_record_creation(self):
        self.assertEqual(self.call_record.sid, "TEST123")
        self.assertEqual(self.call_record.user, self.user)
        self.assertEqual(self.call_record.contact, self.contact)
        self.assertEqual(self.call_record.phone_number, "+1234567890")
        self.assertEqual(self.call_record.duration, 60)
        self.assertEqual(self.call_record.cost, Decimal("1.50"))
        self.assertEqual(self.call_record.status, "completed")
        self.assertIsNotNone(self.call_record.created_at)
        self.assertTrue(timezone.now() >= self.call_record.created_at)
