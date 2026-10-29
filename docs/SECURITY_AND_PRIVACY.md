# Security, Privacy and Incident Response

## Controls built into the system
- Role-based access enforced **on the server** for every private page and file download (students, parents, tutors, finance, administrators each see only what their role needs). Verified by automated tests.
- Email verification; strong password rules (min 10 characters, common-password check); secure password hashing; password change and reset.
- Login rate limiting (django-axes: lock after 5 failed attempts for 1 hour) in production.
- HTTPS enforced, secure cookies, 12-hour sessions, clickjacking and CSRF protection, input validation.
- Uploads: type and size limits, random stored filenames, stored outside the public web folder, served only through permission-checked views.
- Released-results model: marks, feedback and quiz scores are hidden until released.
- Parent access only through administrator-verified links.
- Audit log of finance actions; admission decisions record who/when. Finance records are never hard-deleted.
- No payment credentials, PINs or card data are stored.
- Data export without passwords.

## NOT built in (recommended before handling large volumes of real student data)
1. **Two-factor authentication for administrators** (e.g. django-otp). Until added, give admin/finance accounts long unique passphrases and keep the admin URL private.
2. **Malware scanning of uploads** (e.g. ClamAV on the server).
3. **Automated retention/deletion** of inactive accounts, old applications and documents - the owner must decide retention periods (see below) and a technician can then add a scheduled clean-up.
4. Audit logging beyond finance and admissions decisions (e.g. record exports, role changes).

## Privacy checklist (owner + qualified adviser)
- [ ] Replace the DRAFT Privacy Notice and Terms pages: what data is collected, why, who sees it, how long it is kept, how people request access/correction/deletion.
- [ ] Review Zimbabwean data-protection law (including the Cyber and Data Protection Act) and education/child-safeguarding obligations with a qualified adviser, **before launch**.
- [ ] Decide guardian consent process for learners under 18 (the form already requires guardian details for under-18 applicants).
- [ ] Decide retention periods (applications, documents, messages, reports, financial records).
- [ ] Consent for recorded lessons, photos, testimonials and public student work before using any.
- [ ] Tutor-student communication policy.

## Incident response (suspected data leak, account compromise, or lost device)
1. **Contain**: disable the affected account(s) (Admin area > Users > untick Active); if a server compromise is suspected, take the site offline (`sudo systemctl stop pe`).
2. **Preserve**: do not delete logs; note the time and what was seen. `sudo journalctl -u pe` and nginx logs.
3. **Assess**: what data could have been seen, and whose.
4. **Fix**: change `DJANGO_SECRET_KEY` (logs everyone out), database and email passwords; update software; restore from a clean backup if needed.
5. **Notify**: tell affected people and any legal authority as the law requires (confirm obligations with your adviser).
6. **Review**: record what happened and what will prevent it next time.
