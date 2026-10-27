import stripe
from django.conf import settings


def create_stripe_checkout_session(payment, success_url, cancel_url):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": payment.currency.lower(),
                    "unit_amount": int(payment.amount * 100),
                    "product_data": {
                        "name": f"Payment #{payment.id}",
                    },
                },
                "quantity": 1,
            }
        ],
        metadata={
            "user_id": str(payment.user_id),
            "payment_id": str(payment.id),
        },
        customer_email=payment.user.email,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    payment.stripe_checkout_session_id = session.id
    payment.save(update_fields=["stripe_checkout_session_id"])
    return session
