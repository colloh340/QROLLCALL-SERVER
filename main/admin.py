from django.contrib import admin
from .models import Student, School, Department, Course, Course_Unit, Unit, Lecturer, Attendance, Hash, Timetable, StudentAttendanceRecord

# Register all models in one line
models = [Student, School, Department, Course, Course_Unit, Unit, Lecturer, Attendance, Hash, Timetable, StudentAttendanceRecord]
admin.site.register(models)
