# Professional Edge Online Learning Hub (Django)

Website + student management platform built from the Professional Edge blueprints.
**Start with `docs/00_HANDOVER_SUMMARY.md`** (what is delivered, honest status, handover checklist).

## Quick start (development)
    python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    bash scripts/first_setup.sh     # makes migrations, runs ALL tests, seeds starter data, creates your admin login
    admin
Open http://localhost:8000 (admin area at /admin/ in development). Emails print in the terminal until SMTP is set up.
After first_setup, **commit the generated `migrations/` folders**.

## Documents (docs/)
- 00_HANDOVER_SUMMARY - scope, status, checklist
- DEPLOYMENT - server, HTTPS, backups, restore test, updates
- ADMIN_GUIDE / USER_GUIDES - how to run the system day to day
- SECURITY_AND_PRIVACY - controls, gaps, incident response
- ACCEPTANCE_TESTS - sign-off script
- COSTS_AND_OWNER_DECISIONS, KNOWN_LIMITATIONS

## Apps
core (public site, enquiries) | accounts (users/roles/verification) | admissions (applications, letters) |
learning (courses, resources, assignments) | academics (lessons, attendance, quizzes, reports, parents) |
finance (invoices, manual payments, receipts, audit)

## Useful commands
    python manage.py test              # run before every deployment
    python manage.py setup_groups      # 'Office Staff' permission group
    python manage.py seed_programmes   # starter programmes (unpublished)
    python manage.py export_data       # CSV export of records (no passwords)
    python manage.py check --deploy    # production configuration check
