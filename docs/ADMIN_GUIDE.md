# Office / Administrator Guide

Sign in at the site, then use **Dashboard**. Staff tools live in two places: the **office pages** (Applications, Finance) and the **admin area** at your private admin address (set by `ADMIN_URL`, shown to you by the technician).

## Day-to-day tasks
**1. Review applications** - Dashboard > Applications. Open one, read the details and documents, then choose a decision:
- *Mark under review* / *Put on hold* - no message needed.
- *Request more information* - you must say what is missing; the applicant is emailed and can edit and resubmit.
- *Approve* - enter the approved programme/subjects (e.g. "Cambridge IGCSE English Language 0500"). The applicant becomes a student with a Student ID, an admission-letter PDF becomes available, and they are emailed.
- *Decline* - add a polite note if you wish.
Every decision is recorded with who made it and when.

**2. Enrol an approved student in a course** - Admin area > Courses > open the course > *Enrolments* section > add the student. Students only see courses they are enrolled in.

**3. Create a course** - Admin area > Courses > Add. Set title, exam board, level, assign a tutor, then add *Modules*. Tutors add resources and assignments themselves from their course page.

**4. Create staff accounts** - Admin area > Users > Add. Set **Role**: Tutor, Administrator, or Finance. Give each person their own login. Never share logins. Office administrators who need the Admin area must also have **Staff status** ticked and be added to the **Office Staff** group (created by `python manage.py setup_groups`). Tutors, finance staff, students and parents do not need Staff status. Only the owner/technician should be a *Superuser*.

**5. Link a parent/guardian** - the parent registers normally. In Admin area > Users set their Role to *Parent*, then Admin area > Parent links > Add the learner. **Tick "Verified" only after you have confirmed the relationship** (phone call, ID, or signed consent) and note how in the Note field. Unverified links give no access.

**6. Publish website content** - Admin area > Programmes (tick *published*, set order) and News (Announcements). Starter programmes are created unpublished - review the wording, then publish. Do not publish prices, accreditation or affiliation claims you cannot prove.

**7. Quizzes** - Admin area > Quizzes > Add; add questions inline (A-D options, correct answer, marks). Tick *published*. Scores stay hidden from students/parents until you tick *results released*.

**8. Handle enquiries** - Admin area > Enquiries: change status (New / In progress / Closed) and record who owns it.

## Fees (Finance role or Administrator)
- *Dashboard > Finance*: outstanding, collected this month, overdue, awaiting confirmation.
- **New invoice** for one student, or **Invoice a whole course** (skips students already invoiced for that description).
- When money arrives, open the invoice > **Record a payment** (method + transaction reference). It starts as *Pending*.
- **Check your bank / mobile-money statement**, then press **Confirm** - this issues the numbered receipt. Press **Reject** if the money did not arrive. Decisions are final.
- Never type PINs, card numbers or passwords anywhere.
- An invoice with confirmed payments cannot be cancelled (handle refunds under your written refund policy).

## Records and exports
- Progress reports: open a student's report page and download the PDF.
- Full data export (CSV files, no passwords): the technician runs `python manage.py export_data`. The files contain personal data: keep them private and delete when finished.

## Account safety for staff
Use a long unique password (use the *Password* link to change it). Lock your screen. Log out on shared computers. Report lost devices immediately so the account can be disabled (Admin area > Users > untick *Active*).
