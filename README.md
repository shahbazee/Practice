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

## Notes
- Payments here are records only, no real money moves.
- `db.sqlite3` and `.env` are not committed.
