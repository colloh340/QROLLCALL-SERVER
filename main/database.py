from .models import School, Student, Department, Course,Course_Unit, Lecturer, Unit, Hash, Attendance, StudentAttendanceRecord, StudentUnit
from django.db import IntegrityError
from auth0.views import create_user_account
import datetime
from .utils import location_radius, home_tz
import json

def add_lecturer(data={}):
    if not data:
        return {
            "message": "No data provided",
            "status": 400
        }

    # Extract fields safely
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    department_id = data.get("department_id")

    # Validate required fields
    if not all([first_name, last_name, email, department_id]):
        return {
            "message": "Missing required fields",
            "status": 400
        }

    # Create user account
    success, profile = create_user_account(data)
    
    if not success:
        return profile  # Return error message from create_user_account

    try:
        # Get department
        department = Department.objects.filter(department_id=department_id).first()
        if not department:
            profile.delete()  # Cleanup created user
            return {
                "message": "Invalid department ID",
                "status": 400
            }

        # Create Lecturer entry
        new_lecturer = Lecturer.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            profile=profile,
            user_id=profile.userId
        )

        return {
            "message": f"Successfully added {new_lecturer.first_name}",
            "status": 200
        }

    except IntegrityError:
        profile.delete()  # Cleanup created user if lecturer creation fails
        return {
            "message": "Lecturer ID and email must be unique",
            "status": 400
        }

    except Exception as e:
        profile.delete()  # Cleanup on unexpected errors
        return {
            "message": f"Error occurred: {e}",
            "status": 500
        }

def add_unit(data={}):
    unit_code = data["unit_code"]
    unit_name = data["unit_name"]
    semester_offered = data["semester"]
    department_id = data["department_id"]

    try:
        department = Department.objects.filter(department_id=department_id).first()
        new_unit = Unit(
            unit_code=unit_code,
            unit_name=unit_name,
            department=department,
            semester_offered=semester_offered
        )
        new_unit.save()
        return {
            "message": f"Successfully added {unit_code}",
            "status": 200
        }
    except IntegrityError:
        return {
            "message": "Unit code must be unique", 
            "status": 400
            }
    except Exception as e:
        return {
            "message": f"Error: {e}",
            "status": 405
        }

def add_student_data(data={}):
    if not data:
        return {
            "message": "No data provided",
            "status": 400
        }

    # Extract fields safely
    registration_number = data.get("registration_number")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    department_id = data.get("department_id")
    course_id = data.get("course_id")

    # Validate required fields
    if not all([registration_number, first_name, last_name, email, department_id, course_id]):
        return {
            "message": "Missing required fields",
            "status": 400
        }

    # Create user account
    success, profile = create_user_account(data)

    if not success:
        return profile  # Return error message from create_user_account

    try:
        # Get department and course
        department = Department.objects.filter(department_id=department_id).first()
        course = Course.objects.filter(course_code=course_id).first()

        if not department or not course:
            profile.delete()  # Cleanup created user
            return {
                "message": "Invalid department ID or course ID",
                "status": 400
            }

        # Create Student entry
        student = Student.objects.create(
            registration_number=registration_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            course=course,
            user_id=profile.userId,
            profile=profile
        )

        return {
            "message": f"Successfully added {registration_number}",
            "status": 200
        }

    except IntegrityError:
        profile.delete()  # Cleanup created user if student creation fails
        return {
            "message": "Student email or registration number must be unique",
            "status": 400
        }

    except Exception as e:
        profile.delete()  # Cleanup on unexpected errors
        return {
            "message": f"Error occurred: {str(e)}",
            "status": 500
        }
    
def add_department(data = {}):
    if data:
        school_id = data["school_id"]
        department_name = data["department_name"]
        description = data["description"]
        try:
            # Attempt to create and save the new school
            school = School.objects.filter(school_id=school_id).first()
            new_department = Department(department_name=department_name,department_description=description, school=school)
            new_department.save()
            return {
                "message": "Record added successfully", 
                "status": 201
            }

        except IntegrityError:
            return {
                "message": "Department code must be unique", 
                "status": 400
                }
        except Exception as e:
            # General error handler
            return {
                "message": f"Error occurred: {str(e)}", 
                "status": 500
                }
    else:
        return {
            "message":"Incorrect values",
            "status":400
        }

def add_course(data = {}):
    if data:
        department_id = data["department_id"]
        course_name = data["course_name"]
        try:
            # Attempt to create and save the new school
            department = Department.objects.filter(department_id=department_id).first()
            new_course = Course(course_name=course_name, department=department)
            new_course.save()
            return {
                "message": "Record added successfully", 
                "status": 200
            }

        except IntegrityError:
            return {
                "message": "Course code must be unique", 
                "status": 400
                }
        except Exception as e:
            # General error handler
            return {
                "message": f"Error occurred: {str(e)}", 
                "status": 500
                }
    else:
        return {
            "message":"Incorrect values",
            "status":400
        }

def get_schools_departments_courses(request):
    response = []
    schools = get_schools(request)
    
    if schools is not None:
        for school in schools:
            departments_list = get_school_department(school)
            departments_response = []

            if departments_list is not None:
                for department in departments_list:
                    courses = get_department_courses(department)
                    department_map = {
                        "department": department.department_name,
                        "department_id": department.department_id,
                        "courses": [
                            {
                                "name": course.course_name,
                                "code": course.course_code,
                            } for course in courses
                        ] if courses else []
                    }
                    departments_response.append(department_map)

            school_map = {
                "school": school.school_name,
                "school_id": school.school_id,
                "departments": departments_response,
            }
            response.append(school_map)

    return response

def get_schools(request):
    try:
        return School.objects.all()
    except Exception as e:
        print(f"Error fetching schools: {e}")
        return None

def get_school_department(school):
    try:
        return Department.objects.filter(school=school)  # Fetch all departments for the school
    except Exception as e:
        print(f"Error fetching departments for school {school.name}: {e}")
        return None

def get_department_courses(department):
    try:
        return Course.objects.filter(department=department)  # Fetch all courses for the department
    except Exception as e:
        print(f"Error fetching courses for department {department.name}: {e}")
        return None

def get_all_departments():
    try:
        return Department.objects.all()
    except Exception as e:
        print(f"Error occured {e}")
        return None

def get_all_courses():
    try:
        return Course.objects.all()
    except Exception as e:
        print(f"Error occured {e}")
        return None

def get_course_units(course=None):
    try:
        return Course_Unit.objects.filter(course=course).first() if course else Course_Unit.objects.all()
    except Exception as e:
        print(f"Exception {e}")
        return None

def get_instructors(user_id=None):
    try:
        instructors = Lecturer.objects.filter(user_id=user_id) if user_id else Lecturer.objects.all()
        return [
            {
                "instructor_id": instructor.lecturer_id,
                "instructor_name":f"{instructor.first_name} {instructor.last_name}" 
            } for instructor in instructors
        ]
    except Exception as e:
        print(f"Exception {e}")
        return None
    
def edit_course_unit(course_code, unit_code, add=True):
    try:
        # Fetch course and unit objects
        course = Course.objects.filter(course_code=course_code).first()
        unit = Unit.objects.filter(unit_code=unit_code).first()

        if not course:
            return {"message": "Course does not exist", "status": 400}

        if not unit:
            return {"message": "Unit does not exist", "status": 400}

        # Fetch or create Course_Unit object
        course_unit, _ = Course_Unit.objects.get_or_create(course=course)

        if add:
            if not course_unit.unit.filter(id=unit.id).exists():
                course_unit.unit.add(unit)  # Adds unit to the course
        else:
            course_unit.unit.remove(unit)  # Removes unit from the course

        # Return updated unit list
        units = [
            {"unit_code": u.unit_code, "unit_name": u.unit_name, "department": u.department.department_name}
            for u in course_unit.unit.all()
        ]

        return {
            "message": "Unit added successfully" if add else "Unit removed successfully",
            "course_code": course_code,
            "units": units,
            "status": 200,
        }

    except Exception as e:
        print(f"Exception: {e}")
        return {
            "message": f"An error occurred: {str(e)}",
            "status": 500,
        }


def add_new_attendance(data={}):
    if data:
        attendance_id= data["attendance_id"]
        lecturer= data["lecturer"]
        attendance_date= data["attendance_date"]
        start_time=data["start_time"]
        end_time=data["end_time"]
        unit=data["unit"]
        hash=data["hash"]
        img_data= data["img_data"]
        try:
            new_attedance = Attendance(
                attendance_id=attendance_id,
                lecturer=lecturer,
                attendance_date=attendance_date,
                start_time=start_time,
                end_time=end_time,
                unit=unit
            )
            new_attedance.save()
            new_hash = Hash(
                attendance=new_attedance,
                hash_value=hash
            )
            new_hash.save()
            return {
                    "message":"Qr code generated successfully", 
                    "response":{
                        "img_data": img_data,
                        "attendance_id":attendance_id
                    }, 
                    "status":201
                }
        except Exception as e:
            return {
                {
                    "message":f"Error occurred {e}",
                    "status":500
                }
            }
    else:
        return {
            "message":"Required information not provided",
            "status":200
        }

def db_check_in_attendance(attendance_data, student):
    if not attendance_data or not student:
        return False, {"message": "Incorrect data provided", "status": 405}

    try:
        # Extract required data
        attendance_hash = attendance_data.get("attendance_hash")
        slat, slog = attendance_data.get("slat"), attendance_data.get("slog")

        # Retrieve attendance using hash
        hash_obj = Hash.objects.filter(hash_value=attendance_hash).first()
        if not hash_obj:
            return False, {"message": "Invalid QR code.", "status": 404}

        attendance = hash_obj.attendance
        venue = attendance.venue

        # Convert attendance start and end times to localized datetime
        start_datetime = home_tz.localize(datetime.datetime.combine(attendance.attendance_date, attendance.start_time))
        end_datetime = home_tz.localize(datetime.datetime.combine(attendance.attendance_date, attendance.end_time))
        check_in_time = datetime.datetime.now(tz=home_tz)

        # Verify student location if venue exists
        if venue:
            vlat, vlog = venue.get("vlat"), venue.get("vlog")

            success, response = location_radius({
                "student_location": {"slat": slat, "slog": slog},
                "venue_location": {"vlat": vlat, "vlog": vlog}
            })

            if not success:
                return False, {"message": response.get("message", "Location check failed"), "status": 500}
            
            if response["distance"] > 100:
                return False, {"message": "Not within class range!", "status": 411}

        # Check if attendance is within the valid time range
        if check_in_time < start_datetime:
            return False, {
                "message": f"Class has not started yet. It will start at {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}.",
                "status": 410
            }

        if check_in_time > end_datetime:
            return False, {
                "message": f"Class has already ended. It ended at {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}.",
                "status": 410
            }


        # Register student attendance
        try:
            # Calculate the quarter-time threshold
            class_duration = end_datetime - start_datetime
            quarter_time = class_duration / 4  # 1/4th of class duration

            # Determine attendance status
            if check_in_time <= start_datetime + quarter_time:
                status = "on_time"
            else:
                status = "late"
            StudentAttendanceRecord.objects.create(
                attendance=attendance, 
                student=student, 
                check_in_time=check_in_time, 
                status=status
            )
            
            return True, {"message": "Success", "status": 200}
        except IntegrityError:
            return False, {"message": "Already checked in.", "status": 400}

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return False, {"message": f"Unexpected error: {str(e)}", "status": 500}
    
def get_all_students():
    try:
        return Student.objects.all()
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_all_staffs():
    try:
        staffs = Lecturer.objects.select_related("department").all()
        return staffs
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_all_units():
    try:
        return [
            {
                "unit_code": unit.unit_code,
                "unit_name": unit.unit_name
            } for unit in Unit.objects.all()
        ]
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_scheduled_lectures(unit=None, lecturer=None, date=None, is_ongoing=False, is_student=False, student=None, is_upcoming=False, is_completed=False):
    try:
        # Build filters dynamically
        filters = {}
        if unit:
            filters["unit"] = unit
        if lecturer:
            filters["lecturer"] = lecturer
        if date:
            filters["attendance_date"] = date

        # Optimize database queries: Fetch attendances without unnecessary relations if is_student=True
        attendance_queryset = Attendance.objects.filter(**filters)

        if not is_student:
            attendance_queryset = attendance_queryset.prefetch_related("attendance_student__student")

        response = []
        current_time = datetime.datetime.now(home_tz)  # Get current time once for efficiency
        upcoming = 0

        for attendance in attendance_queryset:
            start_datetime = home_tz.localize(datetime.datetime.combine(attendance.attendance_date, attendance.start_time))
            end_datetime = home_tz.localize(datetime.datetime.combine(attendance.attendance_date, attendance.end_time))

            if start_datetime > current_time:
                upcoming += 1

            # Filter ongoing classes if required
            if is_ongoing and not (start_datetime <= current_time <= end_datetime):
                continue

            if is_completed and not(current_time > end_datetime):
                continue

            if is_upcoming and not(start_datetime > current_time):
                continue

            # Determine class status
            if current_time < start_datetime:
                status = "not-started"
            elif current_time > end_datetime:
                status = "ended"
            else:
                status = "ongoing"

            # Check if the student has checked in
            student_checked_in = False
            if is_student and student:
                student_checked_in = StudentAttendanceRecord.objects.filter(attendance=attendance, student=student).exists()

            # Fetch students only if the request is **not** from a student
            students = []
            if not is_student:
                students = [
                    {
                        "registration_number": record.student.registration_number,
                        "name": f"{record.student.first_name} {record.student.last_name}",
                        "check_in_time": record.check_in_time,
                        "status": record.status
                    }
                    for record in attendance.attendance_student.all()
                ]

            response.append({
                "attendance_id": attendance.attendance_id,
                "attendance_hash": f"attendance_{attendance.attendance_id}",
                "date": attendance.attendance_date,
                "start_time": attendance.start_time,
                "end_time": attendance.end_time,
                "unit_code": attendance.unit.unit_code,
                "unit_name": attendance.unit.unit_name,
                "venue": attendance.venue if attendance.venue else {},
                "status": status,
                "students": students,
                "checked_in": student_checked_in  # Add check-in status
            })

        return upcoming, response

    except Exception as e:
        print(f"Error: {e}")
        return 0, []



def update_attendance_details(attendance_hash, data=None):
    if not attendance_hash:
        return False, {"message": "Invalid attendance hash.", "status": 400}

    data = data or {}
    print(f"Received data: {json.dumps(data, indent=2)}")  # Debugging
    try:
        attendance_entry = Hash.objects.filter(hash_value=attendance_hash).first()
        if not attendance_entry or not attendance_entry.attendance:
            return False, {"message": "Attendance record not found.", "status": 404}

        attendance = attendance_entry.attendance

        if "venue" in data:
            venue = data["venue"]
            new_venue = {
                "vlat": venue.get("vlat"),
                "vlog": venue.get("vlog")
            }
            attendance.venue = new_venue
            attendance.save()
            return True, {"message": "Venue updated successfully.", "status": 200}

        if "schedule" in data:
            schedule = data["schedule"]
            attendance.attendance_date = schedule.get("date")
            attendance.start_time = schedule.get("start_time")
            attendance.end_time = schedule.get("end_time")
            attendance.save()
            return True, {"message": "Class rescheduled successfully.", "status": 200}

        if "status" in data:
            status = data["status"].lower()
            if status in ["stop", "cancel"]:
                attendance.status = status
                attendance.save()
                return True, {
                    "message": "Attendance has been cancelled." if status == "cancel" else "Attendance recording stopped successfully.",
                    "status": 200
                }
            elif status == "delete":
                attendance.delete()
                return True, {"message": "Attendance record deleted.", "status": 200}

        return False, {"message": "No valid update data provided.", "status": 400}

    except Exception as e:
        print(f"Error: {e}")
        return False, {"message": f"Error: {str(e)}", "status": 500}

def get_student_units(student=None):
    try:
        if student is None:
            print("Error: Student not found")
            return False, {
                "message": "Student not found.",
                "status": 400
            }
        
        if not hasattr(student, "student_unit"):
            print("Error: Student has no assigned units")
            return False, {
                "message": "Student has no units.",
                "status": 404
            }
        
        student_units = student.student_unit.units.all()  # Get all related units

        units = [
            {
                "unit_code": unit.unit_code,
                "unit_name": unit.unit_name 
            } for unit in student_units
        ] if student_units.exists() else []

        return True, {
            "message": "Success",
            "status": 200,
            "units": units
        }
    
    except Exception as e:
        print(f"Something went wrong: {e}")
        return False, {
            "message": f"Error: {e}",
            "status": 500
        }
    
    
    
def add_student_unit(user=None, unit_code=None, add=True):
    if not user or not unit_code:
        return False, {"message": "Missing user or unit code", "status": 400}

    try:
        student = Student.objects.filter(profile=user).first()
        if not student:
            return False, {"message": "Student not found.", "status": 404}

        unit = Unit.objects.filter(unit_code=unit_code).first()
        if not unit:
            return False, {"message": f"Unit '{unit_code}' not found.", "status": 404}

        # Get or create the StudentUnit record
        student_units, _ = StudentUnit.objects.get_or_create(student=student)

        # Add the unit only if it does not exist
        if add:
            if student_units.units.filter(id=unit.id).exists():
                return False, {
                    "message": f"Unit '{unit_code}' is already added.",
                    "status": 400
                }
            student_units.units.add(unit)
            return True, {
                "message": f"Success: Unit '{unit_code}' added.",
                "status": 200
            }
        else:
            if not student_units.units.filter(id=unit.id).exists():
                return False, {
                    "message": f"Unit '{unit_code}' is not assigned to the student.",
                    "status": 400
                }
            student_units.units.remove(unit)
            return True, {
                "message": f"Success: Unit '{unit_code}' removed.",
                "status": 200
            }


    except Exception as e:
        print(f"Error: {e}")
        return False, {"message": "Something went wrong.", "status": 500}



