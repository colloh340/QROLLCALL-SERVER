from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Max
import re

# Create your models here.
class School(models.Model):
    school_id = models.CharField(max_length=30, null=False, blank=False, unique=True, default="")
    school_name = models.CharField(max_length=80, null=False, blank=False, unique=True)
    school_description = models.CharField(max_length=250, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.school_id:  # Generate ID only if it's not set
            self.school_id = generate_school_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.school_name

class Department(models.Model):
    department_id = models.CharField(max_length=30, null=False, blank=False, unique=True, default="")
    department_name = models.CharField(max_length=80, null=False, blank=False, unique=True)
    department_description = models.CharField(max_length=250, null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="departments")

    def save(self, *args, **kwargs):
        if not self.department_id:
            self.department_id = generate_department_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.department_name

class Course(models.Model):
    course_code = models.CharField(max_length=30, null=False, blank=False, unique=True, default="")
    course_name = models.CharField(max_length=80, null=False, blank=False, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="courses")

    def save(self, *args, **kwargs):
        if not self.course_code:
            self.course_code = generate_course_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.course_name

class Unit(models.Model):
    unit_code = models.CharField(max_length=30, null=False, blank=False, unique=True)
    unit_name = models.CharField(max_length=80, null=False, blank=False, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="unit_department", null=False, blank=False)
    semester_offered = models.CharField(max_length=10, blank=True, null=True, default=1)

    def __str__(self):
        return self.unit_code
    
class Course_Unit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="unit_course", null=False, blank=False)
    unit = models.ManyToManyField(Unit, related_name="course_units")

    def __str__(self):
        return self.course.course_name
    
class Student(models.Model):
    
    registration_number = models.CharField(max_length=30, null=False, blank=False, unique=True)
    first_name = models.CharField(max_length=30, null=False, blank=False)
    last_name = models.CharField(max_length=30, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    profile = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=False, related_name="student_profile")
    user_id = models.CharField(max_length=100, null=False,unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="student_department", null=False, blank=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="student_course", null=False, blank=False)

    def delete(self, *args, **kwargs):
        """Ensure the associated User is deleted when a Student is deleted."""
        if self.profile:
            self.profile.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.registration_number
    

class Lecturer(models.Model):
    lecturer_id = models.CharField(max_length=30, unique=True, blank=False, default="")
    first_name = models.CharField(max_length=30, null=False, blank=False)
    last_name = models.CharField(max_length=30, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    profile = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=False, related_name="lecturer_profile")
    user_id = models.CharField(max_length=100, unique=True, null=False, blank=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="lecturer_department", null=False, blank=False)

    def save(self, *args, **kwargs):
        """Generate a unique lecturer ID before saving"""
        if not self.lecturer_id:
            self.lecturer_id = generate_staff_id()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Ensure the associated User is deleted when a Lecturer is deleted."""
        if self.profile:
            self.profile.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.lecturer_id
    

class Attendance(models.Model):
    attendance_id = models.CharField(max_length=100, null=False,unique=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, null=False, blank=False, related_name="attendance_lecturer")
    attendance_date = models.DateField(blank=False, null=False)
    start_time = models.TimeField(blank=False, null=False)
    end_time = models.TimeField(blank=False, null=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=False, blank=False, related_name="attendance_unit")
    venue = models.JSONField(blank=True, null=True, default=None)
    status = models.CharField(max_length=20, null=False, blank=False, default="active")

    def __str__(self):
        return f"{self.attendance_date} {self.unit.unit_code}"
    
class Hash(models.Model):
    attendance = models.ForeignKey(Attendance,on_delete=models.CASCADE, null=False, blank=False, related_name="hash_attendance")
    hash_value = models.CharField(max_length=100, null=False, unique=True)

    def __str__(self):
        return f"{self.attendance.attendance_date} {self.attendance.unit.unit_code}"
    
class StudentAttendanceRecord(models.Model):  # Intermediate model
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="attendance_student")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    check_in_time = models.DateTimeField(null=True, blank=True)  # Store check-in timestamp
    status = models.CharField(max_length=20, choices=[('on_time', 'On Time'), ('late', 'Late')], default='on_time')  # Store attendance status

    class Meta:
        unique_together = ('attendance', 'student')  # Prevent duplicate records

    def __str__(self):
        return f"{self.student.registration_number} - {self.attendance.unit.unit_code} - {self.attendance.attendance_date}" 

    
class StudentUnit(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, null=False, blank=False, related_name="student_unit")
    units = models.ManyToManyField(Unit, related_name="student_units")

    def __str__(self):
        return f"{self.student.registration_number}"
    
class Timetable(models.Model):
    unit = models.ForeignKey(Unit,on_delete=models.CASCADE, null=False, blank=False, related_name="timetable_unit")
    start_time = models.TimeField(blank=False, null=False)
    end_time = models.TimeField(blank=False, null=False)
    day = models.CharField(max_length=20, null=False, blank=False)
    venue = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.unit.unit_code

def generate_school_id():
    next_id = _next_prefixed_id(School.objects.values_list("school_id", flat=True), "SCH")
    return f"SCH-{str(next_id).zfill(4)}"

def generate_department_id():
    next_id = _next_prefixed_id(Department.objects.values_list("department_id", flat=True), "DPT")
    return f"DPT-{str(next_id).zfill(4)}"

def generate_course_id():
    next_id = _next_prefixed_id(Course.objects.values_list("course_code", flat=True), "CRS")
    return f"CRS-{str(next_id).zfill(4)}"

def generate_staff_id():
    next_id = _next_prefixed_id(Lecturer.objects.values_list("lecturer_id", flat=True), "STAFF")
    return f"STAFF-{str(next_id).zfill(4)}"


def _next_prefixed_id(existing_ids, prefix):
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    max_numeric_id = 0

    for value in existing_ids:
        if not value:
            continue

        match = pattern.match(value)
        if not match:
            continue

        max_numeric_id = max(max_numeric_id, int(match.group(1)))

    return max_numeric_id + 1
