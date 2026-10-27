import json
import logging

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Payment

logger = logging.getLogger(__name__)


def _event_field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _extract_event(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not sig_header and settings.DEBUG:
        try:
            return json.loads(payload.decode("utf-8")), None
        except Exception:
            return None, HttpResponse(status=400)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event, None
    except ValueError as exc:
        logger.warning(f"Stripe webhook payload error: {exc}")
        return None, HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as exc:
        logger.warning(f"Stripe webhook signature failed: {exc}")
        return None, HttpResponse(status=400)


def _session_and_metadata(event):
    data = _event_field(event, "data", {})
    session = _event_field(data, "object", {})
    metadata = _event_field(session, "metadata", {})
    if hasattr(metadata, "to_dict"):
        metadata = metadata.to_dict()
    return session, metadata


def _find_payment(metadata):
    payment_id = metadata.get("payment_id")
    user_id = metadata.get("user_id")
    if not (payment_id and user_id):
        return None
    try:
        return Payment.objects.get(id=payment_id, user_id=user_id)
    except Payment.DoesNotExist:
        return None


def _handle_checkout_completed(event):
    session, metadata = _session_and_metadata(event)
    payment = _find_payment(metadata)
    if payment is None:
        logger.info("Stripe webhook: payment not found, ignoring")
        return
    if payment.status != Payment.Status.COMPLETED:
        payment.status = Payment.Status.COMPLETED
        payment.stripe_payment_intent_id = _event_field(
            session, "payment_intent"
        )
        payment.save()


def _handle_payment_failed(event):
    session, metadata = _session_and_metadata(event)
    payment = _find_payment(metadata)
    if payment is None:
        return
    if payment.status == Payment.Status.PENDING:
        payment.status = Payment.Status.FAILED
        payment.save()


@csrf_exempt
@require_POST
def stripe_webhook(request):
    event, error_response = _extract_event(request)
    if error_response is not None:
        return error_response
    event_type = _event_field(event, "type")
    if event_type == "checkout.session.completed":
        _handle_checkout_completed(event)
    elif event_type in (
        "checkout.session.expired",
        "payment_intent.payment_failed",
    ):
        _handle_payment_failed(event)
    return HttpResponse(status=200)
