from django.contrib.auth.models import User
from rest_framework import serializers

from api.models import CallRecord, Contact, ContactList


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "first_name", "last_name", "city", "phone_number"]


class ContactListSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = ContactList
        fields = ["id", "name", "contacts"]


class CallRecordSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = CallRecord
        fields = [
            "id",
            "contact",
            "created_at",
            "phone_number",
            "duration",
            "cost",
            "status",
            "sid",
        ]


class AddToContactListSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), many=False, required=False
    )
    contact_list_id = serializers.PrimaryKeyRelatedField(
        queryset=ContactList.objects.all(), many=False, required=False
    )
