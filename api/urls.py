from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AddToContactListViewset,
    CallRecordViewSet,
    ContactListViewSet,
    ContactViewSet,
    TwilioWebhookView,
)

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contact")
router.register(r"contact-lists", ContactListViewSet, basename="contactlist")
router.register(r"call-records", CallRecordViewSet, basename="callrecord")
router.register(
    r"update-contact-list", AddToContactListViewset, basename="updatecontactlist"
)

urlpatterns = [
    path("", include(router.urls)),
    path("twilio-webhook/", TwilioWebhookView.as_view(), name="twilio-webhook"),
]
