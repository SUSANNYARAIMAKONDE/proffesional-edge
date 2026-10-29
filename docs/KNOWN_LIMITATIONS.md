# Known Limitations and Recommendations

**Status:** not yet executed (see `00_HANDOVER_SUMMARY.md` section 2). Migrations must be generated and committed; tests must be run and passed.

## Functional limits (deliberate, for a first release)
- Quizzes: multiple choice only, one attempt, practice use; **not** secure high-stakes examinations.
- Lessons use external meeting links (Zoom/Google Meet); no built-in video, no lesson recording management.
- Payments are **recorded manually**; no online gateway, no automatic reconciliation, single currency (USD). Refunds are handled outside the system.
- Notifications are by email only (no SMS/WhatsApp). The site links to WhatsApp for enquiries.
- Messaging between users, discussion forums, resource versioning history, search/filters on resources and course progress tracking by module are not built.
- Fee statements show invoices and receipts; they do not yet send automatic reminders.
- Reports are per learner (screen/PDF); there is no spreadsheet report builder (use `export_data` and a spreadsheet).
- One application per account; one role per account.
- The homepage does not yet include the blueprint's "Learning Hub preview" and "Why Professional Edge" sections; add them only with claims the organisation can substantiate.

## Technical recommendations (priority order)
1. Run tests, generate/commit migrations, deploy to staging, complete acceptance tests.
2. Add two-factor login for administrators and finance staff.
3. Add malware scanning for uploads and an off-server backup routine.
4. Add scheduled clean-up for inactive accounts once retention periods are decided.
5. Extend audit logging to role changes, data exports and admission-letter generation.
6. Add monitoring/alerts (uptime, disk space, failed backups).
7. Later phases: payment gateway (provider supported in Zimbabwe), SMS/WhatsApp reminders, analytics (privacy-appropriate).
