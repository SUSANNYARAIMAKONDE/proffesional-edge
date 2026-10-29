# Professional Edge Platform - Handover Summary

**Product:** Professional Edge Online Learning Hub - website and student management platform
**Built from:** *Website Technical Blueprint v1.0* and *Growth & Vision Blueprint* (2026)
**Technology:** Python / Django (a mainstream, well-supported framework), PostgreSQL in production, hosted on a standard Linux server.

## 1. What is delivered
| Blueprint phase | Delivered | Where |
|---|---|---|
| 1. Foundation | Branded public site, programmes, news, contact/enquiry management, privacy + terms (DRAFT text) | `core` |
| 2. Accounts & admissions | Registration, email verification, login/reset, application form, private document upload, admin review & decisions, status history, admission-letter PDF | `accounts`, `admissions` |
| 3. Learning Hub | Courses, modules, protected resources (4 access levels), enrolment, assignments, marking, released feedback | `learning` |
| 4. Academic management | Timetable/lessons (Zoom/Meet link), attendance, practice quizzes, progress reports (screen + PDF), parent/guardian portal, tutor self-service | `academics` |
| 5. (part) Fees | Invoices, manual payment recording, reconciliation, PDF receipts, fee statements, audit log | `finance` |
| Operations | Env-based config, PostgreSQL support, login rate limiting, HTTPS enforcement, backups script, data export command, starter programmes, error pages | `config`, `deploy`, `core/management` |
| Quality | 100+ automated tests focused on who-can-see-what and business rules | `*/tests.py` |

**Not included (future phases, by design):** online payment gateway, SMS/WhatsApp notifications, analytics, built-in video conferencing (use Zoom/Google Meet), mobile app.

## 2. HONEST STATUS - read before accepting
The code was written and reviewed, and every Python file and template passes syntax/structure checks. **It has not yet been executed**: the environment it was written in had no Django installation or internet access. That means:

1. Run `scripts/first_setup.sh` on a machine with the requirements installed. It generates the database migrations and runs the whole test suite.
2. If any test fails or an error appears, fix it before anything else. Expect a small number of minor issues on a first run of any new project of this size.
3. **Commit the generated `migrations/` folders** (they do not exist yet).
4. Deploy to a **staging** server, then complete `docs/ACCEPTANCE_TESTS.md` with the owner watching.
5. Only then go live.

Do not treat the project as accepted until steps 1-4 are done and signed off.

## 3. Handover checklist (Blueprint section 12)
| Item | Status |
|---|---|
| Domain & hosting ownership transferred / documented | **Owner action** - see `DEPLOYMENT.md` section 1 |
| Admin accounts delivered securely, no passwords in documents | Create on the server with `createsuperuser`; give credentials in person or via a password manager |
| Source code + configuration documentation | Delivered (this folder) |
| List of plugins, licences, integrations, costs, renewals | `COSTS_AND_OWNER_DECISIONS.md` (fill amounts in) |
| User guides | `ADMIN_GUIDE.md`, `USER_GUIDES.md` |
| Backup, restore, update, security, incident procedures | `DEPLOYMENT.md`, `SECURITY_AND_PRIVACY.md` |
| Data export instructions | `python manage.py export_data` (see `ADMIN_GUIDE.md`) |
| Known limitations & recommendations | `KNOWN_LIMITATIONS.md` |
| Acceptance tests | `ACCEPTANCE_TESTS.md` |
