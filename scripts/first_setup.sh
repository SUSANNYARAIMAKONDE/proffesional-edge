#!/usr/bin/env bash
# One-time setup on a machine that has Python and the requirements installed.
# Run this FIRST, in a development environment, then commit the generated migrations/ folders.
set -euo pipefail
python manage.py makemigrations accounts core admissions learning academics finance
python manage.py migrate
python manage.py test            # every test must pass before you continue
python manage.py setup_groups
python manage.py seed_programmes
python manage.py collectstatic --noinput
python manage.py createsuperuser
echo "Done. Now commit the new migrations/ folders so every server uses identical database structure."
