from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_application, name="my_application"),
    path("edit/", views.application_edit, name="application_edit"),
    path("submit/", views.application_submit, name="application_submit"),
    path("upload/", views.document_upload, name="document_upload"),
    path("document/<int:pk>/", views.document_download, name="document_download"),
    path("letter/<int:pk>/", views.letter_pdf, name="letter_pdf"),
    path("review/", views.review_list, name="review_list"),
    path("review/<int:pk>/", views.review_detail, name="review_detail"),
]
