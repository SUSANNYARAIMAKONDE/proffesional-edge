from django.urls import path
from . import views

urlpatterns = [
    path("", views.student_dashboard, name="student_dashboard"),
    path("course/<int:pk>/", views.course_detail, name="course_detail"),
    path("resource/<int:pk>/", views.resource_download, name="resource_download"),
    path("assignment/<int:pk>/", views.assignment_detail, name="assignment_detail"),
    path("submission/<int:pk>/file/", views.submission_file, name="submission_file"),
    path("tutor/", views.tutor_dashboard, name="tutor_dashboard"),
    path("tutor/course/<int:pk>/", views.tutor_course, name="tutor_course"),
    path("tutor/mark/<int:pk>/", views.mark_submission, name="mark_submission"),
]
