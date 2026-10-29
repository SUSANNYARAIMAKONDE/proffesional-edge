# Acceptance Tests (Blueprint section 12)

Run on the **staging** site with the owner present. Automated coverage is shown where it exists (`python manage.py test` must be fully green first), but each item must still be shown working by hand. Create test accounts: applicant, student, second student, tutor, second tutor, parent, finance, administrator.

| # | Test | Pass? |
|---|---|---|
| 1 | Visitor browses Home, Programmes, Contact; submits an enquiry; staff receive it and the visitor gets an acknowledgement | |
| 2 | New user registers, verifies email, logs in, logs out, resets a forgotten password | |
| 3 | Applicant saves a draft, uploads a document, submits, sees status; admin requests more info; applicant edits and resubmits; admin approves; applicant downloads the admission letter | |
| 4 | Approved student is enrolled and sees the correct course | |
| 5 | Admin adds/edits a programme, course and resource without touching code | |
| 6 | Student can open only their own courses and resources; direct links to others' files/courses fail | |
| 7 | Tutor sees only their courses/students; second tutor cannot open the first tutor's course or marking pages | |
| 8 | Parent sees only the verified linked child; an unverified link shows nothing | |
| 9 | Assignment: submit, mark, give feedback; student sees marks only after release; late/returned work is refused | |
| 10 | Quiz: attempt once, score hidden until released | |
| 11 | Lesson scheduled with meeting link; attendance recorded; report shows attendance | |
| 12 | Invoice created; payment recorded (pending), confirmed, receipt PDF opens; duplicate reference and overpayment refused | |
| 13 | Student/parent see the fee statement; other families' fees are not reachable | |
| 14 | Phone, tablet and laptop layouts look correct on current browsers | |
| 15 | **Backup restored** to a test copy; records and uploaded files open correctly | |
| 16 | `python manage.py check --deploy` shows no serious warnings; five wrong passwords lock the login | |
| 17 | Verification and reset emails arrive in the inbox (not spam) | |

Sign-off: Owner __________________  Technician __________________  Date __________
