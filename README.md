# Practice

Django test project with a payments app and Google sign-in.

## Setup
- Create a virtual environment: `python -m venv .venv`
- Activate it and install dependencies: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and fill in the values
- Apply migrations: `python manage.py migrate`
- Start the server: `python manage.py runserver`

## Google sign-in
- Create OAuth credentials in Google Cloud Console
- Add this redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
- Put the client ID and secret in `.env`
- Open the home page and use "Sign in with Google"

## What is inside
- `config`: Django project settings and URLs
- `payments`: payment records, login required
- Google sign-in via django-allauth

## Stripe hosted checkout (test mode)
- Get test keys from Stripe Dashboard (Developers > API keys)
- Put them in `.env`
- Run Stripe CLI listener for webhooks: `stripe listen --forward-to localhost:8000/payments/webhook/stripe/`
- Put the CLI webhook secret in `.env` as STRIPE_WEBHOOK_SECRET
- Create a payment, press "Pay with Stripe", use test card 4242 4242 4242 4242
- Success page is display only, the webhook marks the payment COMPLETED

## Notes
- Payments here are records only, no real money moves.
- `db.sqlite3` and `.env` are not committed.
