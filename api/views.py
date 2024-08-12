import logging

from celery.result import AsyncResult
from django.conf import settings
from django.shortcuts import get_object_or_404
from django_celery_results.models import TaskResult
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import CallRecord, Contact, ContactList
from api.serializers import (
    AddToContactListSerializer,
    CallRecordSerializer,
    ContactListSerializer,
    ContactSerializer,
)
from api.tasks import dial

logger = logging.getLogger(__name__)


class CallRecordPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ContactViewSet(viewsets.ModelViewSet):

    serializer_class = ContactSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, pk=None):
        contact = get_object_or_404(Contact, pk=pk)
        contact.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContactListViewSet(viewsets.ModelViewSet):
    serializer_class = ContactListSerializer
    perimssion_classes = (IsAuthenticated,)

    def get_queryset(self):
        return ContactList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, pk=None):
        contact_list = get_object_or_404(ContactList, pk=pk)
        contact_list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def dial(self, request, pk=None):
        try:
            contact_list = self.get_object()

            message = request.data.get("message", "")
            if not message:
                return Response(
                    {"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST
                )
            task = dial.delay(contact_list.id, message)

            return Response(
                {
                    "message": f"Initiated calls from {contact_list.name} ",
                    "task_id": task.id,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exception as e:
            logger.error(f"Error in ContactListViewSet dial: {str(e)}")
            return Response(
                {"error": "An error occurred while initiating the calls."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["GET"])
    def latest_task_ids(self, request):
        latest_tasks = TaskResult.objects.filter(task_name="api.tasks.dial").order_by(
            "-date_done"
        )[:5]

        task_ids = [task.task_id for task in latest_tasks]
        return Response({"latest_task_ids": task_ids}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"])
    def check_dial_status(self, request):
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response(
                {"error": "No task_id provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            task_result = AsyncResult(task_id)
            if task_result.ready():
                if task_result.successful():
                    return Response(
                        {"status": "completed", "result": task_result.result},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"status": "failed", "error": str(task_result.result)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                # else:
                #     error_info = task_result.info
                #     return Response({
                #             "status": "failed",
                #             "error": str(error_info.get('exc_message', 'Unknown error')),
                #             "error_type": error_info.get('exc_type', 'Unknown'),
                #             "traceback": error_info.get('traceback', 'No traceback available')
                #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error in check_dial_status: {str(e)}")
            return Response(
                {"error": "An error occurred while checking the dial status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CallRecordFilter(filters.FilterSet):
    contact_name = filters.CharFilter(
        field_name="contact__first_name", lookup_expr="icontains"
    )
    phone_number = filters.CharFilter(
        field_name="phone_number", lookup_expr="icontains"
    )

    class Meta:
        model = CallRecord
        fields = ["contact_name", "phone_number"]


class CallRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CallRecordSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = CallRecordFilter
    filter_backends = [filters.DjangoFilterBackend]
    pagination_class = CallRecordPagination

    def get_queryset(self):
        return CallRecord.objects.filter(user=self.request.user).order_by("-created_at")

    def destroy(self, request, pk=None):
        try:
            call_record = get_object_or_404(CallRecord, pk=pk)
            call_record.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in CallRecordViewSet destroy: {str(e)}")
            return Response(
                {"error": "An error occurred while deleting the call record."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AddToContactListViewset(viewsets.ViewSet):
    serializer_class = AddToContactListSerializer
    permission_classes = (IsAuthenticated,)

    def partial_update(self, request, pk=None, *args, **kwargs):

        try:
            contact_id = request.data.get("contact_id")
            contact_list_id = pk

            if not contact_id or not contact_list_id:
                return Response(
                    {"error": "Both contact_id and contact_list_id are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            contact_list_obj = ContactList.objects.get(id=contact_list_id)
            contact_list_obj.contacts.add(Contact.objects.get(id=contact_id))

            contact_list_obj.save()

            return Response(
                {"message": "Contact list updated"}, status=status.HTTP_200_OK
            )

        except ContactList.DoesNotExist:
            return Response(
                {"error": "Contact list not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Error in AddToContactListViewset partial_update: {str(e)}")
            return Response(
                {"error": "An error occurred while updating the contact list."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TwilioWebhookView(APIView):
    def post(self, request):
        sid = request.data.get("CallSid")
        call_status = request.data.get("CallStatus")
        duration = request.data.get("CallDuration")

        if not sid or not call_status:
            return Response(
                {"error": "CallSid and CallStatus are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            call_record = CallRecord.objects.get(sid=sid)
            call_record.status = call_status

            if duration:
                call_record.duration = int(duration)
            call_record.save()
            logger.info(f"Updated call record for SID: {sid}")
            return Response(status=status.HTTP_200_OK)

        except CallRecord.DoesNotExist:
            logger.error(f"Received webhook for unknown call SID: {sid}")
            return Response(
                {"error": "Call record not found."}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(
                f"Error processing webhook for SID {sid}: {str(e)}", exc_info=True
            )

            return Response(
                {"error": "An error occurred while processing the webhook."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
