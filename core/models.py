from django.db import models


class Programme(models.Model):
    class Category(models.TextChoices):
        HUMANITIES = "humanities", "Humanities"
        SCIENCES = "sciences", "Sciences"
        COMMERCIAL = "commercial", "Commercial & Business Studies"
        SKILLS = "skills", "Professional / Functional Skills"

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=Category.choices)
    exam_board = models.CharField(max_length=60, blank=True, help_text="e.g. Cambridge, ZIMSEC, Edexcel")
    level = models.CharField(max_length=60, blank=True)
    description = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Announcement(models.Model):
    title = models.CharField(max_length=160)
    body = models.TextField()
    published = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title


class Enquiry(models.Model):
    class Category(models.TextChoices):
        ADMISSIONS = "admissions", "Admissions"
        TUITION = "tuition", "Tuition / Programmes"
        RESOURCES = "resources", "Learning Resources"
        SUPPORT = "support", "Technical Support"
        PARTNER = "partner", "Partnerships"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    owner = models.CharField(max_length=120, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "enquiries"

    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"
