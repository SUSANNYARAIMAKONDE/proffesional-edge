from django.contrib import admin
from .models import AuditEntry, Invoice, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("receipt_number", "recorded_by", "confirmed_by")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "student", "description", "amount", "due_date", "cancelled")
    inlines = [PaymentInline]


@admin.register(AuditEntry)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("at", "actor", "action", "detail")
    readonly_fields = [f.name for f in AuditEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
