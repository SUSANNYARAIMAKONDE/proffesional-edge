from django.core.management.base import BaseCommand

from core.models import Programme

# Taken from the Professional Edge blueprints. Everything is created UNPUBLISHED:
# the owner reviews the wording and publishes each programme from the admin area.
PROGRAMMES = [
    ("English Language", "humanities", "Cambridge", "IGCSE / AS & A Level", "Cambridge 9093 / 0500 / 0475 aligned tuition."),
    ("English Literature", "humanities", "Cambridge", "IGCSE / A Level", "Literature set-text and exam-technique support."),
    ("History", "humanities", "Cambridge", "A Level", ""),
    ("Biblical Studies", "humanities", "Cambridge", "A Level", ""),
    ("Psychology", "humanities", "Cambridge", "A Level", ""),
    ("Sociology", "humanities", "Cambridge", "A Level", ""),
    ("Shona", "humanities", "ZIMSEC", "Secondary", ""),
    ("Agriculture", "sciences", "ZIMSEC", "Secondary", ""),
    ("PTE Academic Coaching", "skills", "", "Adult / university applicants",
     "Speaking, Listening, Reading and Writing preparation."),
]


class Command(BaseCommand):
    help = "Create starter programme records (unpublished) from the Professional Edge blueprints. Safe to re-run."

    def handle(self, *args, **opts):
        created = 0
        for i, (name, cat, board, level, desc) in enumerate(PROGRAMMES):
            _, was_new = Programme.objects.get_or_create(
                name=name, defaults=dict(category=cat, exam_board=board, level=level, description=desc, order=i, published=False))
            created += was_new
        self.stdout.write(self.style.SUCCESS(f"{created} programme(s) created, {len(PROGRAMMES) - created} already existed. "
                                             "All are unpublished until you tick 'published' in the admin area."))
