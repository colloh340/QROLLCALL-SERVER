from celery import shared_task
from . import models
from . import report_pdf_generator as pdf
from django.http import HttpResponse
from django.db.models import Count, Q, F, DateTimeField, ExpressionWrapper, Func, Value, CharField
from django.db.models.functions import Concat
from . utils import home_tz
from datetime import datetime
from django.utils.timezone import localtime

@shared_task
def update_student_unit_report(student=None, check_in=None, unit=None):
    if not all([student, check_in, unit]):
        return False, {
            "message": "Missing required fields",
            "status": 400
        }

    try:
        # update student attendance report
        #student_unit_report, _ = models.StudentReport.objects.get_or_create(student=student, unit=unit)

        # get previous attendance
        previous_attendance = models.Attendance.objects.filter(unit=unit)

        total_classes = previous_attendance.count()

    except Exception as e:
        print(f"Error updating report: {e}")
        return False, {
            "message": f"Error: {e}",
            "status": 500
        }
    
def get_attendance_report(attendance_id=None, status="all", time_status="all"):
    if not attendance_id:
        return False, {
            "message": "Missing attendance ID.",
            "status": 400
        }

    try:
        attendance = models.Attendance.objects.select_related(
            "unit", "lecturer"
        ).prefetch_related(
            "attendance_student__student"
        ).get(attendance_id=attendance_id)

        unit = attendance.unit  # Get the unit of the attendance session

        # Get all students taking the unit
        all_students = models.Student.objects.filter(student_unit__units=unit)

        # Get students who checked in
        present_students = set(
            attendance.attendance_student.values_list("student_id", flat=True)
        )

        # Identify absent students
        absent_students = [
            {
                "registration_number": student.registration_number,
                "name": f"{student.first_name} {student.last_name}",
                "check_in_time": "N/A",
                "time_status": "_",
                "status": "Absent"
            }
            for student in all_students if student.id not in present_students
        ]

        # Prepare present students report
        present_students_data = []
        on_time_students = []
        late_students = []

        for record in attendance.attendance_student.all():
            student_data = {
                "registration_number": record.student.registration_number,
                "name": f"{record.student.first_name} {record.student.last_name}",
                "check_in_time": localtime(record.check_in_time, home_tz).strftime("%b, %d at %I:%M %p"),
                "time_status": record.status,
                "status": "Present"
            }
            present_students_data.append(student_data)

            if record.status == "on_time":
                on_time_students.append(student_data)
            elif record.status == "late":
                late_students.append(student_data)

        # Adjust response based on the requested parameters
        filtered_present = present_students_data if status in ["present", "all"] else []
        filtered_absent = absent_students if status in ["absent", "all"] else []
        filtered_on_time = on_time_students if time_status in ["ontime", "all"] else []
        filtered_late = late_students if time_status in ["late", "all"] else []

        # Determine the students list based on requested filters
        if status == "all":
            students_list = filtered_present + filtered_absent
        elif status == "present":
            if time_status == "ontime":
                students_list = filtered_on_time
            elif time_status == "late":
                students_list = filtered_late
            else:
                students_list = filtered_present
        elif status == "absent":
            students_list = filtered_absent
        else:
            students_list = []  # Default case (shouldn't happen)

        # Construct the caption based on filters
        if status == "present" and time_status in ["ontime", "late"]:
            caption = f"Present Students ({time_status.capitalize()})"
        elif status == "present":
            caption = "Present Students"
        elif status == "absent":
            caption = "Absent Students"
        else:
            caption = "Attendance Report"

        report = {
            "attendance_id": attendance_id,
            "unit_code": unit.unit_code,
            "unit_name": unit.unit_name,
            "date": attendance.attendance_date,
            "start_time": attendance.start_time,
            "end_time": attendance.end_time,
            "lecturer": f"{attendance.lecturer.first_name} {attendance.lecturer.last_name}",
            "total_students": all_students.count(),
            "present_count": len(present_students),
            "absent_count": len(absent_students),
            "present_students": filtered_present,
            "absent_students": filtered_absent,
            "on_time_students": filtered_on_time,
            "late_students": filtered_late,
            "students": students_list,  # New field with the filtered list
            "caption": caption,
            "status": 200
        }
        # print(f"Report: {report}")

        return True, report

    except models.Attendance.DoesNotExist:
        print("Requested attendance record not found.")
        return False, {
            "message": "Requested attendance record not found.",
            "status": 404
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        return False, {
            "message": "An error occurred. Try again later.",
            "status": 500,
            "error": str(e)  # Optional, for debugging
        }



def generate_attendance_report_pdf(attendance_id, status="all", time_status="all"):
    is_success, report = get_attendance_report(attendance_id, status=status, time_status=time_status)

    if not is_success:
        return False, HttpResponse(report["message"], status=report["status"])
    
    try:
        status, reponse = pdf.generate_attendance_pdf(report)
        if status:
            return True, reponse
        else:
            return False, HttpResponse("Something went wrong!", status=500)
        
    except Exception as e:
        print(f"Error: {e}")

        return False, HttpResponse("Something went wrong!", status=500)
    

def prepare_staff_report(user=None, staff_id=None, unit_code=None):
    if not (staff_id or user):
        return False, {
            "message": "Missing data",
            "status": 400
        }
    try:
        # Define the filtering condition dynamically
        filter_condition = {"user_id": staff_id} if staff_id else {"profile": user}
        staff = models.Lecturer.objects.filter(**filter_condition).get()

        now = datetime.now(tz=home_tz)

        # Base query for units under this lecturer
        unit_filter = {"attendance_unit__lecturer": staff}
        if unit_code:
            unit_filter["unit_code"] = unit_code  # Filter specific unit

        # Get relevant units
        units = models.Unit.objects.filter(**unit_filter).distinct()

        response_data = {
            "staff_name": f"{staff.first_name} {staff.last_name}",
            "department": staff.department.department_name,
            "email": staff.email,
            "status": 200
        }

        if not units.exists():
            return True, response_data

        # Get attendance counts per unit
        full_datetime_expr = ExpressionWrapper(
            Func(
                Concat(F("attendance_date"), Value(" "), F("end_time")),
                Value("%Y-%m-%d %H:%i:%s"),
                function="STR_TO_DATE",
                output_field=DateTimeField()
            ),
            output_field=DateTimeField()
        )

        # Query attendance records and compute full_end_datetime
        attendance_qs = models.Attendance.objects.filter(
            lecturer=staff, unit__in=units
        ).annotate(
            full_end_datetime=full_datetime_expr
        )

        # Compute aggregate data per unit
        attendance_summary_qs = attendance_qs.values(
            "unit__unit_code", "unit__unit_name"
        ).annotate(
            total_classes=Count("id"),
            completed_classes=Count("id", filter=Q(full_end_datetime__lt=now)),
            uncompleted_classes=Count("id", filter=Q(full_end_datetime__gte=now))
        )

        attendance_dict = {
            unit["unit__unit_code"]: {
                "total_classes": unit["total_classes"],
                "completed_classes": unit["completed_classes"],
                "uncompleted_classes": unit["uncompleted_classes"]
            }
            for unit in attendance_summary_qs
        }

        completed_classes_qs = attendance_qs.filter(full_end_datetime__lt=now).values(
            "id", "unit__unit_code", "unit__unit_name", "attendance_date", "attendance_id",
            "start_time", "end_time", "lecturer__first_name", "lecturer__last_name",
            "full_end_datetime"
        )

        incomplete_classes_qs = attendance_qs.filter(full_end_datetime__gte=now).values(
            "id", "unit__unit_code", "unit__unit_name", "attendance_date", "attendance_id",
            "start_time", "end_time", "lecturer__first_name", "lecturer__last_name",
            "full_end_datetime"
        )

        # Get all students who attended at least once
        student_attendance_qs = models.StudentAttendanceRecord.objects.filter(
            attendance__lecturer=staff, attendance__unit__in=units
        ).values(
            "student__registration_number", "student__first_name", "student__last_name",
            "attendance__unit__unit_code", "attendance__unit__unit_name"
        ).annotate(
            total_attended=Count("id")
        )

        # Get all students officially enrolled in each unit
        student_unit_qs = models.StudentUnit.objects.prefetch_related("units").all()
        student_unit_dict = {}

        for student_unit in student_unit_qs:
            student_reg = student_unit.student.registration_number
            for unit in student_unit.units.all():
                if unit.unit_code not in student_unit_dict:
                    student_unit_dict[unit.unit_code] = []
                student_unit_dict[unit.unit_code].append({
                    "registration_number": student_reg,
                    "name": f"{student_unit.student.first_name} {student_unit.student.last_name}",
                    "total_attended": 0,  # Default, updated if found in attendance_qs
                    "total_absent": 0,  # Will be computed later
                    "compliance_percentage": 0
                })

        # Structure response data per unit
        units_dict = {}
        for unit in units:
            unit_code = unit.unit_code
            units_dict[unit_code] = {
                "unit_code": unit_code,
                "unit_name": unit.unit_name,
                "lecturer_name": f"{staff.first_name} {staff.last_name}",
                "total_classes": attendance_dict.get(unit_code, {}).get("total_classes", 0),
                "completed_classes": attendance_dict.get(unit_code, {}).get("completed_classes", 0),
                "uncompleted_classes": attendance_dict.get(unit_code, {}).get("uncompleted_classes", 0),
                "completed_classes_list": [],
                "uncompleted_classes_list": [],
                "students": [],
                "compliant_students": [],
                "non_compliant_students": [],
                "total_compliance_percentage": 0,
                "total_non_compliance_percentage": 0
            }

        # Group completed and incomplete classes by unit
        for completed in completed_classes_qs:
            unit_code = completed["unit__unit_code"]
            if unit_code in units_dict:
                units_dict[unit_code]["completed_classes_list"].append(completed)

        for incomplete in incomplete_classes_qs:
            unit_code = incomplete["unit__unit_code"]
            if unit_code in units_dict:
                units_dict[unit_code]["uncompleted_classes_list"].append(incomplete)

        # Process student attendance records
        for record in student_attendance_qs:
            unit_code = record["attendance__unit__unit_code"]
            if unit_code in student_unit_dict:
                for student in student_unit_dict[unit_code]:
                    if student["registration_number"] == record["student__registration_number"]:
                        student["total_attended"] = record["total_attended"]

        # Compute attendance & compliance per student
        for unit_code, students in student_unit_dict.items():
            total_classes = attendance_dict.get(unit_code, {}).get("total_classes", 0)

            for student in students:
                student["total_absent"] = total_classes - student["total_attended"]
                student["compliance_percentage"] = round((student["total_attended"] * 100.0) / total_classes, 2) if total_classes > 0 else 0

                if unit_code in units_dict:
                    units_dict[unit_code]["students"].append(student)

                    if student["compliance_percentage"] >= 67:
                        units_dict[unit_code]["compliant_students"].append(student)
                    else:
                        units_dict[unit_code]["non_compliant_students"].append(student)

        # Compute compliance percentages per unit
        for unit in units_dict.values():
            total_students = len(unit["students"])
            compliant_count = len(unit["compliant_students"])
            non_compliant_count = len(unit["non_compliant_students"])

            unit["total_compliance_percentage"] = round((compliant_count / total_students) * 100, 2) if total_students else 0
            unit["total_non_compliance_percentage"] = round((non_compliant_count / total_students) * 100, 2) if total_students else 0

        response_data["units"] = list(units_dict.values())

        return True, response_data

    except models.Lecturer.DoesNotExist:
        return False, {
            "message": "Lecturer not found",
            "status": 404
        }
    except Exception as e:
        print(f"Error: {e}")
        return False, {
            "message": "Something went wrong",
            "status": 500
        }

def generate_staff_report_pdf(type="all",user=None, staff_id=None, unit_code=None):
    if not(user or staff_id) or not unit_code:
        return False, HttpResponse("Missing data.", status=400)
    
    is_success, report = prepare_staff_report(user=user, staff_id=staff_id, unit_code=unit_code)

    if not is_success:
        return False, HttpResponse(report["message"], status=report["status"])
    
    try:
        report["report_type"] = type
        
        status, reponse = pdf.generate_staff_unit_report(report)
        if status:
            return True, reponse
        else:
            return False, HttpResponse("Something went wrong!", status=500)
    except Exception as e:
        print(f"Error: {e}")
        return False, HttpResponse("Something went wrong!", status=500)
        

def prepare_student_report(student_reg=None, unit_code=None):
    if not student_reg:
        return False, {"message": "Missing student registration number", "status": 400}

    try:
        student = models.Student.objects.select_related('department', 'course').get(registration_number=student_reg)

        student_units = models.StudentUnit.objects.filter(student=student).prefetch_related('units')
        units = student_units.first().units.all() if student_units.exists() else []

        if unit_code:
            units = units.filter(unit_code=unit_code)

        # Fetch attendance data in bulk
        attendance_records = models.StudentAttendanceRecord.objects.filter(
            student=student, attendance__unit__in=units
        ).select_related('attendance', 'attendance__lecturer', 'attendance__unit')

        unit_attendance_data = {}
        for record in attendance_records:
            unit_id = record.attendance.unit.id
            if unit_id not in unit_attendance_data:
                unit_attendance_data[unit_id] = []

            unit_attendance_data[unit_id].append({
                "attendance_id": record.attendance.attendance_id,
                "attendance_date": record.attendance.attendance_date,
                "start_time": record.attendance.start_time,
                "end_time": record.attendance.end_time,
                "lecturer": f"{record.attendance.lecturer.first_name} {record.attendance.lecturer.last_name}",
                "status": "Present",
                "check_in_time": localtime(record.check_in_time, home_tz).strftime("%b, %d at %I:%M %p"),
                "time_status": record.status.capitalize()
            })

        # Fetch all attendance sessions (including those where the student was absent)
        all_attendance_sessions = models.Attendance.objects.filter(unit__in=units).select_related("lecturer", "unit")

        report = {
            "student": {
                "name": f"{student.first_name} {student.last_name}",
                "registration_number": student.registration_number,
                "department": student.department.department_name,
                "course": student.course.course_name
            },
            "units": []
        }

        for unit in units:
            unit_attendance = []
            total_sessions = 0
            attended_count = 0
            late_count = 0
            on_time_count = 0

            for attendance in all_attendance_sessions.filter(unit=unit):
                total_sessions += 1
                student_attendance_list = unit_attendance_data.get(unit.id, [])

                student_attendance = next((a for a in student_attendance_list if a["attendance_id"] == attendance.attendance_id), None)

                if student_attendance:
                    attended_count += 1
                    if student_attendance["time_status"] == "On_time":
                        on_time_count += 1
                    else:
                        late_count += 1
                    unit_attendance.append(student_attendance)
                else:
                    unit_attendance.append({
                        "attendance_id": attendance.attendance_id,
                        "attendance_date": attendance.attendance_date,
                        "start_time": attendance.start_time,
                        "end_time": attendance.end_time,
                        "lecturer": f"{attendance.lecturer.first_name} {attendance.lecturer.last_name}",
                        "status": "Absent",
                        "check_in_time": "N/A",
                        "time_status": "_"
                    })

            missed_count = total_sessions - attended_count
            compliance_percentage = (attended_count / total_sessions * 100) if total_sessions > 0 else 0
            compliance_status = "Compliant" if compliance_percentage >= 67 else "Non-Compliant"

            report["units"].append({
                "unit_name": unit.unit_name,
                "unit_code": unit.unit_code,
                "total_sessions": total_sessions,
                "attended_count": attended_count,
                "missed_count": missed_count,
                "on_time_count": on_time_count,
                "late_count": late_count,
                "compliance_percentage": round(compliance_percentage, 2),
                "compliance_status": compliance_status,
                "attendance_details": unit_attendance
            })
        #print(f"Report: {report}")
        return True, report

    except models.Student.DoesNotExist:
        print(f"Student not found")
        return False, {"message": "Student not found", "status": 404}
    except Exception as e:
        print(f"Error occurred. {e}")
        return False, {"message": "Something went wrong.", "status": 500}
