# Deployment Guide (Linux VPS + nginx + gunicorn + PostgreSQL)

Audience: the technician who sets up the server. Any reputable VPS with Ubuntu 22.04/24.04 works.

## 1. Ownership first (do this before building anything online)
Register the domain (e.g. professionaledge.co.zw) and the hosting account **in the owner's name** and email. Record in `COSTS_AND_OWNER_DECISIONS.md`: registrar, hosting provider, account email, renewal dates. A technician must never be the only holder of these accounts.

## 2. Server setup
```bash
sudo apt update && sudo apt install -y python3-venv python3-dev build-essential nginx postgresql libpq-dev certbot python3-certbot-nginx git
sudo adduser --system --group --home /srv/professional_edge pe
sudo -u postgres psql -c "CREATE USER pe_user WITH PASSWORD 'CHANGE-ME';"
sudo -u postgres psql -c "CREATE DATABASE professional_edge OWNER pe_user;"
```
Copy the project to `/srv/professional_edge`, then:
```bash
cd /srv/professional_edge
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env        # fill in every value; chmod 600 .env
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py setup_groups            # creates the 'Office Staff' permission group
python manage.py seed_programmes         # optional starter programmes (unpublished)
python manage.py check --deploy          # review any warnings
```
(Migrations must already be committed - see `00_HANDOVER_SUMMARY.md` section 2.)

## 3. Run the app
```bash
sudo cp deploy/pe.service /etc/systemd/system/ && sudo systemctl enable --now pe
sudo cp deploy/nginx.conf /etc/nginx/sites-available/professional_edge
sudo ln -s /etc/nginx/sites-available/professional_edge /etc/nginx/sites-enabled/
sudo certbot --nginx -d professionaledge.co.zw -d www.professionaledge.co.zw   # free HTTPS certificate, auto-renews
sudo nginx -t && sudo systemctl reload nginx
```
Point the domain's DNS A records at the server's IP address.

## 4. Email
Use a reliable email provider (SMTP) and add the SPF and DKIM records it gives you to the domain's DNS, otherwise verification emails may land in spam. Set `EMAIL_*`, `DEFAULT_FROM_EMAIL`, and `STAFF_NOTIFY_EMAIL` in `.env`. Test: register a new account and confirm the verification email arrives.

## 5. Backups (mandatory)
```bash
sudo -u pe mkdir -p /srv/professional_edge/backups
sudo -u pe crontab -e      # add:  30 2 * * * /srv/professional_edge/deploy/backup.sh >> /var/log/pe-backup.log 2>&1
```
- Keep 14 days on the server (the script does this) **and copy backups off the server** to a second location (cloud storage or another machine). Agree with the owner who checks this weekly.
- **Restore test (do before launch, then every quarter):** on a spare machine/database:
  ```bash
  gunzip -c db.sql.gz | psql -h localhost -U pe_user professional_edge_test
  tar -xzf private_media.tar.gz          # restores uploaded files
  ```
  Log in and confirm a student record, an uploaded document and a receipt open correctly. Record the date of each successful restore test.

## 6. Updating the site
1. Take a backup. 2. Test the change on a staging copy. 3. On the server: `git pull` (or copy files), `source venv/bin/activate`, `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py collectstatic --noinput`, `sudo systemctl restart pe`. 4. Check the site. Keep the previous version so you can roll back (restore DB backup if a migration must be undone).
Apply operating-system and Python package security updates monthly.

## 7. Monitoring
`sudo journalctl -u pe -n 100` shows application errors. Use a free uptime monitor on the home page and set it to alert the owner by email.

## 8. Default-secret checklist (must all be true)
- [ ] `DJANGO_DEBUG=0` and a long random `DJANGO_SECRET_KEY`
- [ ] No default or shared admin logins; each staff member has their own account
- [ ] `ADMIN_URL` changed from `admin/`
- [ ] `.env` is `chmod 600` and not in the code repository
- [ ] Database not reachable from the internet (PostgreSQL listens on localhost only)
- [ ] `private_media/` is not served directly by nginx
- [ ] A restore test has succeeded
