# CLAUDE.md

## Project
Django test project. `config` is the project package. `payments`
is the only app. Google sign-in uses django-allauth.

## Code rules
- PEP 8, maximum 79 characters per line.
- No comments and no docstrings in code.
- Keep files small and structure minimal. Do not add files
  that are not needed for the task.
- Use function-based views for simple pages and class-based
  views only where Django gives a clear advantage.

## Secrets
- Secrets live only in `.env`, never in code.
- Never commit `.env`. Copy `.env.example` to `.env` and fill
  in real values locally.
- Never print or paste secret values in chat or commit messages.

## Workflow
- Run `python manage.py check` before committing.
- Stage files by name, never blind `git add .`.
- Run `python manage.py test` before pushing.

## How to run
- Create a virtual environment and install requirements.
- Copy `.env.example` to `.env` and set the values.
- Run migrations, then `python manage.py runserver`.
