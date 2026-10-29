from django.urls import path
from . import views

urlpatterns = [
    path("timetable/", views.timetable, name="timetable"),
    path("timetable/<int:student_id>/", views.timetable, name="child_timetable"),
    path("quiz/<int:pk>/", views.quiz_detail, name="quiz_detail"),
    path("report/<int:student_id>/", views.report, name="report"),
    path("report/<int:student_id>/pdf/", views.report_download, name="report_pdf"),
    path("parent/", views.parent_dashboard, name="parent_dashboard"),
    path("parent/child/<int:student_id>/", views.child_view, name="child_view"),
    path("tutor/course/<int:pk>/lessons/", views.tutor_lessons, name="tutor_lessons"),
    path("tutor/lesson/<int:pk>/attendance/", views.attendance_register, name="attendance_register"),
    path("tutor/course/<int:pk>/resource/add/", views.tutor_resource_add, name="tutor_resource_add"),
    path("tutor/course/<int:pk>/assignment/add/", views.tutor_assignment_add, name="tutor_assignment_add"),
]
