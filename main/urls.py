from django.urls import path, include
from . import views

app_name = "main"
urlpatterns = [
    path("", view=views.index, name=""),
    path("dashboard/", view=views.dashboard_view, name="dashboard"),
    path("android_home", views.android_home, name="android_home"),
    
    path("attendance/schedule",views.schedule_class_view, name="schedule_class_view"),
    path("attendance/schedule/page", views.schedule_new_view, name="schedule_new"),
    path("attendance/check_in",views.check_in_attendance, name="check_in_attendance"),
    path("attendance/update",views.update_attendance_view, name="update_attendance"),
    path("attendance/report", views.attendance_report_view, name="attendance_report"),

    path("student", views.admin_student_view, name="student_view"),
    path("student/report", views.student_report, name="student_report"),
    path("students/add", views.add_student_view, name="add_student"),
    path("student/units", views.student_unit_view, name="student_units"),
    path("schools/add", views.add_school, name="add_school"),

    path("lecturer", views.admin_lecturer_view, name="lecturer_view"),
    path("lecturer/create", views.add_lecturer_view_page, name="add_lecturer_view_page"),
    path("lecturer/add", views.add_lecturer_view, name="add_lecturer"),
    path("lecturer/report", views.staff_unit_report, name="staff_unit_report"),

    path("department/add", views.add_department_view, name="add_department"),
    path("courses", views.get_courses_view, name="get_courses"),
    path("courses/<course_code>/units/<todo>", views.course_units, name="course_unit"),
    path("course/units", views.get_course_units_view, name="get_course_units"),
    path("course/add", views.add_course_view, name="add_course"),
    path("units/add", views.add_unit_view, name="add_unit"),
    path("scheduled", views.scheduled_view_filters, name="scheduled"),
    path("android/scheduled", views.android_scheduled_view, name="android_scheduled_view"),
    path("student/attendance", views.student_unit_summary, name="student_unit_summary"),

    path("profile", views.profile_view, name="profile_view"),    
]