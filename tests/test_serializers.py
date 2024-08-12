from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from api.models import CallRecord, Contact, ContactList
from api.serializers import (
    AddToContactListSerializer,
    CallRecordSerializer,
    ContactListSerializer,
    ContactSerializer,
)


class SerializerTests(TestCase):
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

    def test_contact_serializer(self):
        serializer = ContactSerializer(instance=self.contact)
        self.assertEqual(serializer.data["first_name"], "John")
        self.assertEqual(serializer.data["last_name"], "Doe")
        self.assertEqual(serializer.data["city"], "Test City")
        self.assertEqual(serializer.data["phone_number"], "+1234567890")

    def test_contact_list_serializer(self):
        serializer = ContactListSerializer(instance=self.contact_list)
        self.assertEqual(serializer.data["name"], "Test List")
        self.assertIn(self.contact.id, serializer.data["contacts"])

    def test_call_record_serializer(self):
        serializer = CallRecordSerializer(instance=self.call_record)
        self.assertEqual(serializer.data["phone_number"], "+1234567890")
        self.assertEqual(serializer.data["duration"], 60)
        self.assertEqual(serializer.data["cost"], "1.50")
        self.assertEqual(serializer.data["status"], "completed")
        self.assertEqual(serializer.data["contact"]["first_name"], "John")
        self.assertIn("created_at", serializer.data)

    def test_add_to_contact_list_serializer(self):
        data = {"name": "New List", "contact_id": self.contact.id}
        serializer = AddToContactListSerializer(data=data)
        self.assertTrue(serializer.is_valid())
