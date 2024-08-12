import logging

from django.conf import settings
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from api.models import CallRecord, ContactList

logger = logging.getLogger(__name__)


class TwilioDialerService:
    def __init__(self, account_sid, auth_token):

        self.client = Client(account_sid, auth_token)

    def dialContactList(
        self,
        contact_list_id,
        message,
        from_number=getattr(settings, "TWILIO_PHONE_NUMBER"),
    ):
        if not from_number:
            logger.error("TWILIO_PHONE_NUMBER is not set in settings")
            raise ValueError("TWILIO_PHONE_NUMBER is not set")

        try:
            contact_list = ContactList.objects.get(id=contact_list_id)
        except contact_list.DoesNotExist:
            logger.error(f"ContactList with id {contact_list_id} does not exist")
            raise ValueError(f"ContactList with id {contact_list_id} does not exist")

        callRecords = []

        for contact in contact_list.contacts.all():
            # breakpoint()
            personalized_message = message.replace("{first_name}", contact.first_name)
            personalized_message = personalized_message.replace(
                "{last_name}", contact.last_name
            )
            personalized_message = personalized_message.replace("{city}", contact.city)
            personalized_message = personalized_message.replace(
                "{phone_number}", contact.phone_number
            )

            logger.info(f"MESSAGE IS {personalized_message}")

            callObject = self.__dial(
                contact.phone_number, personalized_message, from_number
            )
            # logger.info(f"{callObject.price}")
            try:
                callRecords.append(
                    CallRecord.objects.create(
                        user=contact_list.user,
                        contact=contact,
                        phone_number=contact.phone_number,
                        duration=int(callObject.duration) if callObject.duration else 0,
                        cost=abs(float(callObject.price)) if callObject.price else 0,
                        status=callObject.status,
                        sid=callObject.sid,
                    )
                )
                # use the time from twilio api

                # return True
            except Exception as e:
                logger.error(
                    f"Error processing contact {contact.id}: {str(e)}", exc_info=True
                )
        try:
            CallRecord.objects.bulk_create(
                callRecords,
                batch_size=5000,
                ignore_conflicts=True,
                unique_fields=["sid"],
            )
        except Exception as e:
            logger.error(f"Error bulk creating CallRecords: {str(e)}", exc_info=True)
            raise e

    def __dial(self, phone_number, message, from_number):

        try:
            response = VoiceResponse()
            response.say(message, voice="Woman", language="en-US")
            response.play("https://api.twilio.com/cowbell.mp3")

            call = self.client.calls.create(
                to=str(phone_number),
                from_=from_number,
                twiml=str(response),
                status_callback="https://mako-lucky-apparently.ngrok-free.app/api/twilio-webhook/",
                status_callback_method="POST",
            )

            return call

        except TwilioRestException as e:
            error_message = f"Twilio error while dialing {phone_number}: {str(e)}"
            logger.error(error_message, exc_info=True)
            return error_message
        except Exception as e:
            error_message = f"Error encountered while dialing {phone_number}: {str(e)}"
            logger.error(error_message, exc_info=True)
            return error_message
