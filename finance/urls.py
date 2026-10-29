from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="finance_dashboard"),
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/new/", views.invoice_create, name="invoice_create"),
    path("invoices/course/", views.invoice_course, name="invoice_course"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/cancel/", views.invoice_cancel, name="invoice_cancel"),
    path("payments/<int:pk>/<str:decision>/", views.payment_decide, name="payment_decide"),
    path("receipt/<int:pk>/", views.receipt_pdf, name="receipt_pdf"),
    path("my-fees/", views.fee_statement, name="my_fees"),
    path("fees/<int:student_id>/", views.fee_statement, name="child_fees"),
]
