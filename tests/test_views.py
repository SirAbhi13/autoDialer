from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import CallRecord, Contact, ContactList


class ViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
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

    def test_list_contacts(self):
        url = reverse("contact-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_contact(self):
        url = reverse("contact-list")
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "city": "New City",
            "phone_number": "+0987654321",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 2)

    def test_list_contact_lists(self):
        url = reverse("contactlist-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch("api.tasks.dial.delay")
    def test_dial_contact_list(self, mock_dial):
        mock_dial.return_value.id = "test_task_id"
        url = reverse("contactlist-dial", args=[self.contact_list.id])
        data = {"message": "Test message"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)

    def test_list_call_records(self):
        url = reverse("callrecord-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_add_to_contact_list(self):
        new_contact = Contact.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Doe",
            city="Another City",
            phone_number="+0987654321",
        )
        url = reverse("updatecontactlist-detail", args=[self.contact_list.id])
        data = {"contact_id": new_contact.id}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact_list.refresh_from_db()
        self.assertIn(new_contact, self.contact_list.contacts.all())

    def test_twilio_webhook(self):
        url = reverse("twilio-webhook")
        data = {"CallSid": "TEST123", "CallStatus": "completed", "CallDuration": "120"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.call_record.refresh_from_db()
        self.assertEqual(self.call_record.status, "completed")
        self.assertEqual(self.call_record.duration, 120)
