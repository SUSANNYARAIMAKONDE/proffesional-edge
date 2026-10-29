from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

APPS = ["core", "admissions", "learning", "academics", "finance"]


class Command(BaseCommand):
    help = "Create/refresh the 'Office Staff' group: manage site content, admissions, courses, quizzes and fees in the admin area."

    def handle(self, *args, **opts):
        group, _ = Group.objects.get_or_create(name="Office Staff")
        perms = Permission.objects.filter(content_type__app_label__in=APPS).exclude(
            content_type__app_label="finance", content_type__model="auditentry")
        audit_view = Permission.objects.filter(content_type__app_label="finance", codename="view_auditentry")
        users = Permission.objects.filter(content_type__app_label="accounts", codename__in=["view_user", "add_user", "change_user"])
        group.permissions.set(list(perms) + list(audit_view) + list(users))
        self.stdout.write(self.style.SUCCESS(f"'Office Staff' group ready with {group.permissions.count()} permissions. "
                                             "Add staff to it and tick 'Staff status' on their user record."))


