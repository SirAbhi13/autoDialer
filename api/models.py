from django.contrib.auth.models import User
from django.db import models


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    phone_number = models.CharField(
        max_length=20,
    )  # make phone number unique for a user

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=["user", "phone_number"]),
            models.Index(fields=["user", "city"]),
        ]
        unique_together = ["user", "phone_number"]


class ContactList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    contacts = models.ManyToManyField(Contact)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["user", "name"]),
        ]


class CallRecord(models.Model):
    sid = models.CharField(max_length=100, unique=True)  # unique=true
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20)
    duration = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f" Call to {self.contact} at {self.time}"

    class Meta:
        indexes = [
            models.Index(fields=["sid"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "status"]),
        ]
