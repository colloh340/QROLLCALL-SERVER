from django.shortcuts import render
from  .qr_code_generator import QR
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.core.serializers import serialize
import json
from .generate_hash import Generator
from django.views.decorators.csrf import csrf_exempt
from decouple import config
import datetime
from auth0.jwt_token import decode_jwt
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .database import(
    add_student_data, add_lecturer, add_new_attendance, add_course, add_unit, get_schools_departments_courses, 
    get_all_courses, get_all_departments,
    add_department,get_schools, get_course_units, get_instructors, edit_course_unit, db_check_in_attendance, get_all_students, 
    get_all_units, get_scheduled_lectures, update_attendance_details, get_student_units, add_student_unit
    ) 
from .models import School, Student, Course, Unit, Lecturer, Attendance, StudentAttendanceRecord
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .utils import is_admin, is_staff, is_student, home_tz
from auth0.utils import check_auth, verify_client
from django.db.models import Count, Q
from . import reports
from django.contrib.auth import authenticate

APP_NAME = config("APP_NAME", default=None)
SECRET_KEY = config("SECRET_KEY", default="B85GBWT84VUD32JBCLA5RA5N")

# Create your views here.
def index(request):
    user = request.user
    return render(request, "landing_page.html", {"user": user})

@csrf_exempt
def android_home(request):
    is_verified, response = check_auth(request)
    if not is_verified:
        return JsonResponse(response, status=response["status"])

    try:
        user = get_user_model().objects.get(email=response["email"])

        if is_student(user):
            response.update(get_student_info(user))

        elif is_staff(user):
            response.update(get_staff_info(user))

        return JsonResponse(response, status=response["status"])

    except Exception as e:
        return JsonResponse({"message": f"Error: {e}", "status": 500}, status=500)


def get_student_info(user):
    """Fetch student-related information."""
    try:
        student = Student.objects.filter(profile=user).first()
        return {
            "course": student.course.course_name,
            "course_code": student.course.course_code,
            "department": student.department.department_name,
            "department_code": student.department.department_id,
            "registration_number": student.registration_number,
            "school_name": student.department.school.school_name,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "email": student.profile.email,
            } if student else {}
    except Exception as e:
        raise Exception(f"Failed to fetch student information: {e}")


def get_staff_info(user):
    """Fetch staff-related information."""
    try:
        staff = Lecturer.objects.filter(profile=user).first()
        if not staff:
            return {}

        current_date = datetime.datetime.now(tz=home_tz).date()
        _,attendances = get_scheduled_lectures(lecturer=staff, date=current_date)

        return {
            "department": staff.department.department_name,
            "schedule_today": attendances if attendances else [],
        }
    except Exception as e:
        raise Exception(f"Failed to fetch staff information: {e}")

@login_required(login_url='/auth/login/web')
def dashboard_view(request):
    user = request.user

    if request.method == "GET":
        try:
            is_admin_user = is_admin(user)
            is_staff_user = is_staff(user)
            additional_info = {}

            if is_admin_user:
                additional_info = {
                    "total_students": get_all_students().count(),
                    "total_courses": get_all_courses().count(),
                    "total_staff": len(get_instructors()),
                    "total_units": len(get_all_units()),
                }

            elif is_staff_user:
                lecturer = Lecturer.objects.filter(profile=user).first()
                rq_get = request.GET.get("get", None)
                if rq_get:
                    is_success, report = reports.prepare_staff_report(user=user)
                    if is_success:
                        print(f"Report: {report}")
                        return JsonResponse({"report": report, "status": 200}, status=200)
                    return JsonResponse(report, status=report.get("status") or 500)
                if not lecturer:
                    return JsonResponse({
                        "message": "Staff info cannot be found!",
                        "status": 404
                    }, status=404)

                _,attendances = get_scheduled_lectures(lecturer=lecturer)
                current_date = datetime.datetime.now(tz=home_tz).date()
                previous_classes, upcoming_classes, today_classes = [], [], []

                if isinstance(attendances, list):
                    for attendance in attendances:
                        status = attendance["status"]
                        if status == "ongoing":
                            today_classes.append(attendance)
                        elif status == "ended":
                            previous_classes.append(attendance)
                        else:
                            upcoming_classes.append(attendance)

                additional_info.update({
                    "today_classes": len(today_classes),
                    "previous_classes": len(previous_classes),
                    "upcoming_classes": len(upcoming_classes),
                    "today": today_classes,
                    "previous": previous_classes,
                    "upcoming": upcoming_classes
                })

            return render(request, "index.html", {
                "user_object": user,
                "is_admin": is_admin_user,
                "is_staff": is_staff_user,
                "additional_info": additional_info
            })

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({
                "message": "Server error occurred!",
                "status": 500
            }, status=500)

    return JsonResponse({"message": "Invalid request"}, status=400)

def generate_qr_code(request):
    if request.method  != "GET":
        return HttpResponseForbidden("Not permitted")
    
    attendance_id = request.GET.get("attendance", None)

    if attendance_id is None:
        return JsonResponse({"message": "Mising data", "status":"400"}, status=400)
    
    try:
        attendance = Attendance.objects.select_related(
            "unit"
        ).filter(attendance_id=attendance_id).first()

        if attendance is None:
            return render(request, "404.html", {})
        
        qr = QR(f"attendance_{attendance.attendance_id}", attendance.unit.unit_code, attendance.attendance_date)

        img_base64 = qr.generate_qr_code()

        return render(request, "qr_code_viewer.html", {
            "qr_code": img_base64,
            "attendace_id": attendance_id
        })

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"message": "Something went wrong!", "status":500}, status=500)
    

def schedule_class_view(request):
    user = request.user
    if is_staff(user):
        if request.method == "POST":
            unit_code = request.POST.get("input-unit", "").strip()
            course_code = request.POST.get("input-course", "").strip()
            start_time = request.POST.get("input-start-time", "").strip()
            end_time = request.POST.get("input-end-time", "").strip()
            date = request.POST.get("input-date", "").strip()

            # Ensure no field is empty
            if not all([unit_code, course_code, start_time, end_time, date]):
                return JsonResponse({"message": "All fields are required.", "status": 400}, status=400)

            try:
                # Fetch related objects
                instructor = Lecturer.objects.filter(profile=user).first()
                if not instructor:
                    return JsonResponse({"message": "Instructor not found.", "status": 400}, status=400)
                course = Course.objects.filter(course_code=course_code).first()
                if not course:
                    return JsonResponse({"message": "Invalid course selected.", "status": 400}, status=400)
                unit = Unit.objects.filter(unit_code=unit_code).first()
                if not unit:
                    return JsonResponse({"message": "Invalid unit selected.", "status": 400}, status=400)

                # Generate QR code
                attendance_id = Generator(unit_code)
                class_hashes = f"attendance_{attendance_id}"
                qr = QR(class_hashes, unit.unit_code, date)
                img_base64 = qr.generate_qr_code()

                if img_base64:
                    new_attendance_map = {
                        "attendance_id": str(attendance_id),
                        "lecturer": instructor,
                        "attendance_date": date,
                        "start_time": start_time,
                        "end_time": end_time,
                        "unit": unit,
                        "hash": class_hashes,
                        "img_data": img_base64,
                    }
                    response = add_new_attendance(new_attendance_map)
                    return JsonResponse(response, status=201)
                else:
                    return JsonResponse({"message": "Failed to generate QR code.", "status": 500}, status=500)

            except Exception as e:
                return JsonResponse({"message": f"Error occurred: {str(e)}", "status": 500}, status=500)

            
        elif request.method == "GET":
            course_units = get_course_units()

            response = {
                "course_unit": [],
                "instructors": [] 
            }

            if course_units:
                for course_unit in course_units:
                    course = course_unit.course
                    units = course_unit.unit.all() or []  # Default to empty list if units is None
                    unit_list = []
                    for unit in units:
                        unit_list.append({
                            "course": course.course_name,
                            "course_code": course.course_code,
                            "unit_code": unit.unit_code,
                            "unit_name": unit.unit_name
                        })
                    course_unit_map = {
                        "course": course.course_name,
                        "course_code": course.course_code,
                        "units": unit_list
                    }
                    response["course_unit"].append(course_unit_map)
                
                return JsonResponse({"message": "success", "response": response, "status": 201})
            else:
                return JsonResponse(
                    {
                        "message": "Cannot process request at the moment",
                        "response": response,
                        "status": 500
                    }, 
                )


    return HttpResponseForbidden("No permission to access this services.")

@login_required(login_url='/auth/login/web')
def schedule_new_view(request):
    user = request.user
    is_admin_user = is_admin(user)
    is_staff_user = is_staff(user)
    if is_staff_user:
        return render(request,"schedule_new.html", {"is_staff": is_staff_user, "is_admin": is_admin_user})
    return HttpResponseForbidden("Not allowed to access this page.")

@csrf_exempt
def check_in_attendance(request):
    is_verified, response = check_auth(request)

    if not is_verified:
        return JsonResponse(response, status=response["status"])
    else:
        User = get_user_model()
        user = User.objects.get(email=response["email"])
        if request.method == "POST":
            try:
                # Get the raw body of the request
                raw_body = request.body
                data = json.loads(raw_body)
                attendance_hash = data.get("attendance_hash", None)
                slat = data.get("slat")
                slog = data.get("slog")
                print(f"Latitude: {slat}, Longitude: {slog}")
                if is_student(user):
                    try:
                        student = Student.objects.filter(profile=user).first()
                        if attendance_hash is not None and attendance_hash.startswith("attendance"):
                            # Check if the student is within the location radius
                                
                            result, res = db_check_in_attendance({
                                "attendance_hash": attendance_hash,
                                "slat": slat,
                                "slog": slog
                            }, student)

                           
                            return JsonResponse(res, status=res["status"])
                        else:
                            return JsonResponse({
                                "message":"Invalid data provided!",
                                "status": 405
                            }, status=405)
                    except Exception as e:
                        print(f"Error: {e}")
                        return JsonResponse({
                            "message": f"Error: {e}",
                            "status":500
                        },status=500)
                else:
                    return JsonResponse({
                        "message":"Unauthorised. Not a student",
                        "status":401
                    }, status=401)
                
            except json.JSONDecodeError:
                print("Failed to parse JSON")
                return JsonResponse({"error": "Invalid JSON format"}, status=400)
        return JsonResponse({"error": "Invalid method"}, status=405)

@login_required(login_url="/auth/login/web")  
def admin_student_view(request):
    user = request.user

    is_user_admin= is_admin(user)

    if not is_user_admin:
        return HttpResponseForbidden("Not allowed to view this page.")
    
    try:
        if request.method != "GET":
            return HttpResponse("This  method is not allowed")
        page = request.GET.get("page", 1)  # Default to page 1 if not provided
        students = Student.objects.select_related("department", "course").all()
        
        paginator = Paginator(students, 50)  # 50 lecturers per batch

        try:
            students_batch = paginator.page(page)
        except:
            return JsonResponse({"error": "Invalid page number"}, status=400)

        students_data = [
            {
                "registration_number": student.registration_number,
                "name": f"{student.first_name} {student.last_name}",
                "email": student.email,
                "course": student.course.course_name,
                "department": student.department.department_name
            }
            for student in students_batch
        ]
        
        return render(request, "admin_students.html", {
            "is_admin": is_user_admin,
            "students": students_data,
            "has_next": students_batch.has_next(),  # Check if more pages exist
            "page": page,
        })
        
    except Exception as e:
        print(f"Something went wrong!")
        return HttpResponse("Something wrong, try again later")

@csrf_exempt
def add_student_view(request):
    is_verified, verification_response = verify_client(request)
    
    if not is_verified:
        return JsonResponse(verification_response, status=verification_response["status"])
    
    if request.method == "GET":
        response = get_schools_departments_courses(request)
        return JsonResponse({"message": "Success", "response": response, "status": 200})

    elif request.method == "POST":
        # Extract student data based on content type
        student_data, error_response = extract_student_data(request)
        if error_response:
            return JsonResponse(error_response, status=400)

        # Add additional required fields
        student_data.update({
            "type_id": "student",
            # "password": student_data["registration_number"],  # Set password as reg number
            "account_created_on": datetime.datetime.now().date(),
            "image_url": ""
        })

        # Process and add student data
        response = add_student_data(student_data)
        return JsonResponse(response, status=response["status"])

    return JsonResponse({"message": "Method not allowed", "status": 405}, status=405)

@login_required(login_url="/auth/login/web")
def student_report(request):
    user = request.user
    is_user_admin = is_admin(user)
    is_user_staff = is_staff(user)

    if not(is_user_admin or is_user_staff):
        return HttpResponseForbidden("Not allowed to view this page")
    
    if request.method != "GET":
        return HttpResponse("Method not allowed!")
    
    student_reg_no = request.GET.get("u", None)
    unit_code = request.GET.get("s", None)
    full_report = request.GET.get("full", "false").lower().strip() == "true"

    if not student_reg_no:
        return HttpResponse("Missing student data")
    
    is_sucess, report = reports.prepare_student_report(student_reg=student_reg_no, unit_code=unit_code)

    if not is_sucess:
        return JsonResponse(report, status=report["status"])
    
    if full_report and unit_code:
        return render(request, "student_unit_detailed.html", {"report": report, "is_admin": is_user_admin, "is_staff": is_user_staff})

    return render(request, "student_unit_report.html", {"report": report, "is_admin": is_user_admin, "is_staff": is_user_staff})


# **Helper Function to Extract Student Data**
def extract_student_data(request):

    try:
        if request.content_type == "application/json":
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = {
                "registration_number": request.POST.get("input-reg-no"),
                "first_name": request.POST.get("input-first-name"),
                "last_name": request.POST.get("input-last-name"),
                "email": request.POST.get("input-email"),
                "department_id": request.POST.get("input-department"),
                "course_id": request.POST.get("input-course"),
                "password": request.POST.get("password") or request.POST.get("input-reg-no")
            }
        
        # Ensure all required fields are provided
        if not all(data.values()):
            return None, {"message": "All fields are required", "status": 400}

        return data, None

    except json.JSONDecodeError:
        return None, {"message": "Invalid JSON format", "status": 400}

def add_school(request):
    if request.user.is_authenticated and is_admin(request.user) :
        if request.method == "POST":
            school_name = request.POST.get("input-school-name")
            school_description = request.POST.get("input-school-description")
            # Check if school_id and school_name are provided
            if not school_name:
                return JsonResponse({"message": "School name required", "status": 400})

            try:
                # Attempt to create and save the new school
                new_school = School(school_name=school_name, school_description=school_description)
                new_school.save()
                return JsonResponse({"message": "Record added successfully", "status": 201}, status=201)

            except IntegrityError:
                return JsonResponse({"message": "School code must be unique", "status": 400})
            except Exception as e:
                # General error handler
                return JsonResponse({"message": f"Error occurred: {str(e)}", "status": 500})
        
        else:
            return JsonResponse({"message": "Invalid method.", "status": 405}, status=405)
    return HttpResponseForbidden("You are not authorized to access this page. Login as admin")

def add_department_view(request):
    user = request.user
    if user.is_authenticated and  is_admin(user):
        if request.method == "POST":
            school_id = request.POST.get("input-school")
            department_name = request.POST.get("input-department-name")
            department_description = request.POST.get("input-department-description")

            if school_id and department_name:
                department_map = {
                    "department_name":department_name,
                    "school_id": school_id,
                    "description":department_description
                }
                response = add_department(department_map)
                return JsonResponse(response)
            return JsonResponse({
                "message":"All required fields not provided",
                "status": 400
            })    
        elif request.method == "GET":
            schools = get_schools(request)
            response = []
            if schools is not None:
                return JsonResponse({
                    "message":"sucess", 
                    "response": 
                    [
                        {
                            "school": school.school_name,
                            "school_id": school.school_id
                         } for school in schools
                    ],
                    "status":200
                    })
            return JsonResponse({"message":"cant process request at the moment","response": response, "status":500})
        else:
            return JsonResponse({"message":"Bad request", "status":400})

    return HttpResponseForbidden("You are not authorized to access this page. Login as admin")

def add_unit_view(request):
    user = request.user
    if user.is_authenticated and is_admin(user):
        if request.method == "POST":
            unit_code = request.POST.get("input-unit-code")
            unit_name = request.POST.get("input-unit-name")
            department = request.POST.get("input-department")
            semester = request.POST.get("input-semester")

            if unit_code and unit_name and department:
                unit_map = {
                    "unit_code": unit_code,
                    "unit_name":unit_name,
                    "department_id":department,
                    "semester": semester if semester else 1
                }
                response = add_unit(unit_map)

                return JsonResponse(response, status=200)
            else:
                return JsonResponse({
                    "message":"Unit code, name and department are required!",
                    "status":405
                })
        elif request.method == "GET":
            response = {
                "message": "Empty list",
                "status": 405,
                "response": []
            }
            departments = get_all_departments()
            if departments:
                response["message"] = "Success"
                response["status"] = 200
                response["response"] = [
                    {
                        "department_id": department.department_id,
                        "department": department.department_name
                    }
                    for department in departments
                ]
            return JsonResponse(response, status=response["status"])

        else:
            return {
                "message":"Bad request",
                "status":400
            }
    return HttpResponseForbidden("You are not authorized to access this page. Login as admin")

def add_course_view(request):
    user = request.user
    if user.is_authenticated and  is_admin(user):
        if request.method == "POST":
            course_name = request.POST.get("input-course-name")
            department = request.POST.get("input-department")
            if course_name and department:
                course_map = {
                    "course_name":course_name,
                    "department_id": department
                }
                response = add_course(course_map)
                return JsonResponse(response, status=response["status"])
            else:
                return JsonResponse({
                "message":"All required fields not provided",
                "status": 400
            })

        elif request.method == "GET":
            departments = get_all_departments()
            response = []
            if departments is not None:
                return JsonResponse({
                    "message":"sucess", 
                    "response": 
                    [
                        {
                            "department": department.department_name,
                            "department_id": department.department_id
                         } for department in departments
                    ],
                    "status":200
                    })
            return JsonResponse({"message":"cant process request at the moment","response": response, "status":500})
        else:
            return JsonResponse({"message":"Bad request", "status":400})

    return HttpResponseForbidden("You are not authorized to access this page. Login as admin")

@login_required(login_url="/auth/login/web")
def admin_lecturer_view(request):

    if request.method != "GET":
        return HttpResponse("Method not allowed!")
    
    user = request.user
    is_user_admin = is_admin(user)
    
    if not is_user_admin:
        return HttpResponseForbidden("Not allowed to view page")
    
    """
    Fetch lecturers in batches of 50.
    """
    page = request.GET.get("page", 1)  # Default to page 1 if not provided
    lecturers = Lecturer.objects.select_related("department").all()
    
    paginator = Paginator(lecturers, 50)  # 50 lecturers per batch

    try:
        lecturer_batch = paginator.page(page)
    except:
        return JsonResponse({"error": "Invalid page number"}, status=400)

    lecturer_data = [
        {
            "lecturer_id": lecturer.user_id,
            "name": f"{lecturer.first_name} {lecturer.last_name}",
            "email": lecturer.email,
            "department": lecturer.department.department_name
        }
        for lecturer in lecturer_batch
    ]
    
    return render(request, "admin_staff.html", {
        "is_admin": is_user_admin,
        "staffs": lecturer_data,
        "has_next": lecturer_batch.has_next(),  # Check if more pages exist
        "page": page,
    })

def add_lecturer_view_page(request):
    user = request.user
    is_user_staff = is_staff(user)
    is_user_admin = is_admin(user)
    return render(request, 'add_staff.html', {
        "is_admin": is_user_admin,
        "user": user,
        "is_staff": is_user_staff
    })
    
def add_lecturer_view(request):
    user = request.user
    #if request.user.is_authenticated and is_admin(request.user):
    if request.method == "GET":
        response = get_schools_departments_courses(request)
        return JsonResponse({"message":"Success","response": response, "status":200})
    elif request.method == "POST":
        password = request.POST.get("password")
        first_name = request.POST.get("input-first-name")
        last_name = request.POST.get("input-last-name")
        email = request.POST.get("input-email")
        department_id = request.POST.get("input-department")
        account_created_on = datetime.datetime.now(tz=home_tz).date()
        if password and first_name and last_name and email:
            lecturer_map = {
                "first_name": first_name,
                "last_name": last_name,
                "email":email,
                "department_id": department_id,
                "type_id": "staff",
                "password": password,
                "account_created_on": account_created_on,
                "image_url": ""
            }
            response = add_lecturer(lecturer_map)
            if not user.is_authenticated:
                response.update({"redirect_url": "/auth/login/web"}) 
            return JsonResponse(response, status=response.get("status", 200))
        else:
            return JsonResponse({"message":"All fields required", "status":400}, status=400)
            
    #return HttpResponseForbidden("You are not authorized to access this page. Login as admin")

def get_courses_view(request):
    user = request.user
    if user.is_authenticated and is_admin(user):
        if request.method == "GET":
            response = {
                "message":"Empty list",
                "response": [], # Initialize the list here
                "status": 400
            }
            courses = get_all_courses()
            if courses:
                for course in courses:
                    course_unit = get_course_units(course)
                    units = []

                    if course_unit is not None:
                        unit_data = course_unit.unit.all() or []
                        for unit in unit_data:
                            units.append({
                                "unit_code": unit.unit_code,
                                "unit_name": unit.unit_name,
                                "department": unit.department.department_name
                            })

                    response["response"].append({
                        "course_name": course.course_name,
                        "course_code": course.course_code,
                        "units": units
                    })
                response["status"] = 200
            else:
                response["status"] = 404  # In case there are no courses

            return JsonResponse(response, status=response["status"])

    else:
        return HttpResponseForbidden("You are not authorized to access this page")

def course_units(request, course_code, todo):
    if not course_code or not todo:
        return JsonResponse({"message": "Course code and action required", "status": 400}, status=400)

    user = request.user
    if not user.is_authenticated or not is_admin(user):
        return HttpResponseForbidden("Not allowed to access this page")

    if request.method != "POST":
        return JsonResponse({"message": "Invalid request method", "status": 400}, status=400)

    unit_code = request.POST.get("unit_code")
    if not unit_code:
        return JsonResponse({"message": "Unit code is required", "status": 400}, status=400)

    response = edit_course_unit(course_code, unit_code, todo.lower() == "add")
    return JsonResponse(response, status=response["status"])

@login_required(login_url="/auth/login/web")
def scheduled_view_filters(request):
    user = request.user
    is_user_admin = is_admin(user)
    is_user_staff = is_staff(user)

    if user.is_authenticated and is_user_admin or is_user_staff:
        if request.method == "GET":
            try:
                units = []
                all_units = get_all_units()
                if isinstance(all_units, list):
                    units = all_units

                status = request.GET.get("status", None)
                unit_code = request.GET.get("unit_code", None)
                date = request.GET.get("date", None)
            
                if not(status or unit_code or date):
                    date = str(datetime.datetime.now(tz=home_tz).date())

                if (status or unit_code or date):

                    if not is_user_staff:
                        return HttpResponseForbidden("Request not allowed")
                    
                    unit =None
                    lecturer = None
                    is_ongoing = False
                    is_upcoming = False
                    is_completed = False
                    req_date = None

                    caption = ''

                    if unit_code and unit_code != "":
                        caption += "Unit: " +unit_code
                        unit = Unit.objects.filter(unit_code=unit_code).first()
                    
                    if status and status != "":
                        if status == "ongoing":
                            caption = "ongoing classes"
                            is_ongoing = True
                        elif status == "upcoming":
                            caption = "upcoming classes"
                            is_upcoming = True
                        elif status == "completed":
                            caption = "completed classes"
                            is_completed = True
                    
                    if date and date != "":
                        caption += " Date: "+date
                        req_date = date

                        
                    lecturer = Lecturer.objects.filter(profile=user).first()

                    _, attendance_reponse = get_scheduled_lectures(unit=unit, date=req_date, lecturer=lecturer, is_ongoing=is_ongoing, is_upcoming=is_upcoming, is_completed=is_completed)

                    return render(request, "schedules.html",{
                        "caption": caption,
                        "attendances": attendance_reponse,
                        "is_admin": is_user_admin,
                        "is_staff": is_user_staff,
                        "units": units
                    })
                
                return HttpResponse("Something went wrong")
                
            except Exception as e:
                print(f"Error units: {e}")
                return JsonResponse({
                    "message": f"Error: {e}",
                    "status": 500
                },status=500)
        return JsonResponse({"message":"Invalid method"}, status=405)
    return HttpResponseForbidden("You are not authorized to access this page. Login as admin")

@csrf_exempt
def update_attendance_view(request):
    if request.method == "POST":
        is_verified, response = check_auth(request)
        if not is_verified:
            return JsonResponse(response, status=response["status"])

        try:
            user = get_user_model().objects.get(email=response["email"])

            if is_staff(user) or is_admin(user):
                raw_body = request.body
                print(f"Status: {raw_body}")

                data = json.loads(raw_body)
                status = data.get("status", None)
                slat = data.get("slat", None)
                slog = data.get("slog", None)
                date = data.get("date", None)
                start_time = data.get("start_time", None)
                end_time = data.get("end_time", None)
                attendance_hash = data.get("attendance_hash", None)
                data_map = {}
                if status:
                    data_map["status"] = status
                elif(slat and slog):
                    venue = {
                        "vlat":slat,
                        "vlog":slog
                    }
                    data_map["venue"] = venue
                elif(date and start_time and end_time):
                    schedule = {
                        "date":date,
                        "start_time":start_time,
                        "end_time":end_time
                    }
                    data_map["schedule"] = schedule
                if attendance_hash:
                    is_sucess, results = update_attendance_details(attendance_hash,data_map)
                    return JsonResponse(results, status=results["status"])
                else:
                    return JsonResponse({"message":"Incorrect data", "status":400}, status=400)
            else:
                return JsonResponse({"message":"Unauthorised!", "status":401},status=401)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"message": f"Error: {e}", "status": 500}, status=500)
    else:
        return JsonResponse({"message": "Invalid method!", "status": 400}, status=400)
    
def get_course_units_view(request):
    if request.method == "GET":
        try:
            course_name = request.GET.get("course_name", None)
            course_code = request.GET.get("course_code", None)
            filters = {}

            if course_code:
                filters["course_code"] = course_code

            if course_name:
                filters["course_name"] = course_name  # Fixed assignment

            # Using related_name="unit_course"
            course = Course.objects.filter(**filters).prefetch_related("unit_course").first()

            if course is None:
                return JsonResponse({
                    "message": "Course not found.",
                    "status": 404
                }, status=404)

            # If unit_course is a related set (OneToMany), get all related units
            course_units = course.unit_course.first().unit.all()  # Assuming OneToMany relationship

            if course_units is None:
                print("No units assigned to course")
                return JsonResponse({
                    "message": "No units assigned to course",
                    "status": 200,
                    "response": []
                }, status=200)

            # Extract units
        

            print(f"Units: {course_units}")
            return JsonResponse({
                "message": "Success",
                "status": 200,
                "response": [
                    {
                        "unit_code": unit.unit_code,
                        "unit_name": unit.unit_name
                    } for unit in course_units
                ]
            }, status=200)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({
                "message": f"Error occurred: {e}",
                "status": 500
            }, status=500)
        
@csrf_exempt
def student_unit_view(request):
    is_verified, response = check_auth(request)

    if not is_verified:
        return JsonResponse(response, status=response["status"])
  
    email = response["email"]

    User = get_user_model()

    user = User.objects.get(email=email)

    if user is None:
        return JsonResponse({
            "message": "Something went wrong. No account associated to email.",
            "status": 401
        }, status=401)
    
    if request.method != "POST":
        try:

            student = Student.objects.filter(profile=user).select_related("student_unit").first()
            
            _ ,student_units_res = get_student_units(student)
            print(f"Student units: {student_units_res}")
            return JsonResponse(student_units_res, status=student_units_res["status"])
        
        except Exception as e:
            print(f"Error occured: {e}")
            return JsonResponse({
                "message": "Failed to get units",
                "status": 500,
            }, 500)
    else:
        try:
            # add unit to student

            data = json.loads(request.body.decode("utf-8"))

            unit_code = data.get("unit_code")

            op = data.get("op")

            if unit_code is None:
                return JsonResponse({
                    "message":"Unit code is required",
                    "status": 400,
                }, status=400)
            
            if op is None:
                return JsonResponse({
                    "message":"Operation (add, remove) missing",
                    "status": 400,
                }, status=400)
            add = True if op == "add" else False

            is_sucess, add_remove_res = add_student_unit(user=user, unit_code=unit_code, add=add)

            return JsonResponse(add_remove_res, status=add_remove_res["status"])
        
        except Exception as e:
            print(f"Error occured: {e}")
            return JsonResponse({
                "message": "Failed to get units",
                "status": 500,
            }, 500)

@csrf_exempt
def android_scheduled_view(request):
    is_verified, response = check_auth(request)
    if not is_verified:
        return JsonResponse(response, status=response["status"])

    try:
        user = get_user_model().objects.get(email=response["email"])

        # Parse date correctly
        date_str = request.GET.get("date")
        if date_str:
            try:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"message": "Invalid date format. Use YYYY-MM-DD.", "status": 400}, status=400)
        else:
            date = datetime.datetime.now(tz=home_tz).date()

        # Convert is_ongoing to boolean
        is_ongoing = request.GET.get("on_going", "false").strip().lower() == "true"

        response_data = []
        upcoming=0

        if is_student(user):
            # Fetch student and units efficiently
            student = Student.objects.select_related("profile").prefetch_related("student_unit__units").filter(profile=user).first()

            if student is None or not hasattr(student, "student_unit"):
                return JsonResponse({
                    "message": "Student not found or has no assigned units.",
                    "status": 400
                }, status=400)

            student_units = student.student_unit.units.all()

            if not student_units.exists():
                return JsonResponse({
                    "message": "No units assigned to student",
                    "status": 200,
                    "response": []
                }, status=200)

            # Get attendance for each unit
            for unit in student_units:
                upcoming,unit_attendance = get_scheduled_lectures(unit=unit, date=date, is_ongoing=is_ongoing,is_student=True, student=student)
                if isinstance(unit_attendance, list):
                    response_data.extend(unit_attendance)

        elif is_staff(user):
            lecturer = Lecturer.objects.filter(profile=user).first()
            if lecturer is None:
                return JsonResponse({
                    "message": "Staff not found.",
                    "status": 404
                }, status=404)

            upcoming,attendance = get_scheduled_lectures(lecturer=lecturer, date=date)
            if isinstance(attendance, list):
                response_data.extend(attendance)

        return JsonResponse({
            "message": "Success",
            "status": 200,
            "response": response_data,
            "upcoming": upcoming
        }, status=200)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"message": f"Error: {str(e)}", "status": 500}, status=500)

def student_unit_summary(request):
    is_verified, response = verify_client(request)

    if not is_verified:
        return JsonResponse(response, status=response["status"])
    
    if request.method != "GET":
        return JsonResponse({"message": "Invalid method", "status": 405}, status=405)
    
    userID = request.GET.get("userID")

    if not userID:
        return JsonResponse({"message": "User ID required", "status": 400}, status=400)
    
    try:
        student = Student.objects.prefetch_related("student_unit").filter(user_id=userID).first()

        if not student:
            return JsonResponse({"message": "Student not found", "status": 404}, status=404)

        # Fetch all units the student is enrolled in
        student_units = student.student_unit.units.all()

        summary_response = []

        for unit in student_units:
            # Count total lectures for this unit
            total_lectures = Attendance.objects.filter(unit=unit).count()

            # Get attendance stats for the student in this unit
            attendance_stats = (
                StudentAttendanceRecord.objects.filter(student=student, attendance__unit=unit)
                .aggregate(
                    total_attendances=Count("attendance"),
                    on_time=Count("id", filter=Q(status="on_time")),
                    late=Count("id", filter=Q(status="late"))
                )
            )

            present = attendance_stats.get("total_attendances", 0) or 0
            absent = total_lectures - present
            on_time = attendance_stats.get("on_time", 0) or 0
            late = attendance_stats.get("late", 0) or 0

            unit_summary = {
                "unit_code": unit.unit_code,
                "unit_name": unit.unit_name,
                "total_lectures": total_lectures,
                "present": present,
                "absent": absent,
                "on_time": on_time,
                "late": late
            }
            summary_response.append(unit_summary)

        return JsonResponse({"message":"Success","response": summary_response, "status": 200}, status=200)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({
            "message": "An unexpected error occurred.",
            "status": 500
        }, status=500)       

@login_required(login_url="/auth/login/web")
def attendance_report_view(request):
    user = request.user
    is_user_admin = is_admin(user)
    is_user_staff = is_staff(user)

    if not (is_user_staff or is_user_admin):
        return HttpResponseForbidden("Not allowed to view this page.")

    
    if request.method != "GET":
        return HttpResponseForbidden("Method not allowed")

    attendance_id = request.GET.get("attendance", None)
    get= request.GET.get("get", None)
    data_type = request.GET.get("type", None)
    qr_filter = request.GET.get("filter", "false").lower().strip() == "true"
    qr_status = request.GET.get("status", "all")
    qr_time = request.GET.get("time", "all")

    if not attendance_id:
        return render(request, "404.html", {})
    
    # prepare attendance report
    if attendance_id and get:
        if get == "pdf":
            _, report = reports.generate_attendance_report_pdf(attendance_id, qr_status, qr_time)

            return report
        
        elif get == "qr":

            attendance = Attendance.objects.select_related(
                "unit"
            ).filter(attendance_id=attendance_id).first()

            if attendance is None:
                return render(request, "404.html", {})
            
            qr = QR(f"attendance_{attendance.attendance_id}", attendance.unit.unit_code, attendance.attendance_date)

            img_base64 = qr.generate_qr_code()

            if data_type and data_type == "pdf":
                is_success, response = qr.generate_qr_pdf(img_base64)

                if is_success:
                    return response
                
                return HttpResponse("Something went wrong! It us not you.")

            return render(request, "qr_code_viewer.html", {
                "attendance_id": attendance_id,
                "qr_code": img_base64
            })

    is_success, report = reports.get_attendance_report(attendance_id = attendance_id,  status=qr_status, time_status=qr_time)

    if not is_success:
        return render(request, "404.html", {})
    
    if qr_filter:
        return JsonResponse({"report": report})

    return render(request, "unit_attendance_reports.html", {
        "report": report,
        "is_admin": is_user_admin,
        "is_staff": is_user_staff
    })

@login_required(login_url="/auth/login/web")
def staff_unit_report(request):
    user = request.user

    is_user_admin = is_admin(user)
    is_user_staff = is_staff(user)

    if not (is_user_admin or is_user_staff):
        return HttpResponseForbidden("Not allowed to view this page.")

    if request.method != "GET":
        return HttpResponse("Invalid request.")

    staff_id = request.GET.get("u", None)
    unit_code = request.GET.get("s", None)  # Get unit code from the query params
    full = request.GET.get("f", "false").strip().lower() == "true"
    pdf = request.GET.get("pdf", "false").strip().lower() == "true"
    type_report = request.GET.get("type", "all")

    if not (staff_id or is_user_staff):
        return HttpResponse("Lecturer not found.")

    try:
        if is_user_staff:
            if pdf:
                _, report = reports.generate_staff_report_pdf(user=user, unit_code=unit_code, type=type_report)
                return report
            is_success, report = reports.prepare_staff_report(user=user, unit_code=unit_code)
        else:
            if pdf:
                _, report = reports.generate_staff_report_pdf(staff_id=staff_id, unit_code=unit_code, type=type_report)
                return report
            is_success, report = reports.prepare_staff_report(staff_id=staff_id, unit_code=unit_code)

        if not is_success and not report["status"] == 400:
            print(f"Report: {report}")
            return HttpResponse(f"Something went wrong. {report['message']}")

        staff_id = user.userId if is_user_staff else staff_id
        
        #print(f"Report: {report}")


        return render(
            request,
            "report_unit_staff.html" if not full else "staff_unit_detailed.html",
            {
                "report": report,
                "is_staff": is_user_staff,
                "is_admin": is_user_admin,
                "staff_id": staff_id,
            },
        )

    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Something went wrong.")
    
@login_required(login_url="/auth/login/web")
def profile_view(request):
    user = request.user
    is_user_admin = is_admin(user)
    is_user_staff = is_staff(user)
    if request.method == "GET":
        try:
            if is_user_staff:
                lecturer = Lecturer.objects.filter(profile=user).first()
                if not lecturer:
                    return render(request, "404.html", {"message": "Staff not found!"}, status=404)
                qs_user = {
                    "first_name": lecturer.first_name,
                    "last_name": lecturer.last_name,
                    "email": lecturer.email,
                    "department": lecturer.department.department_name if lecturer.department else "Not assigned"
                }
            elif is_user_admin:
                qs_user = user

            return render(request, "account.html", {"user": user,"qs_user": qs_user, "is_admin": is_user_admin, "is_staff":is_user_staff})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"message": "Something went wrong. Try again later.", "status": 500}, status=500)
    elif request.method == "POST":
        old_password = request.POST.get("old_password", None)
        new_password = request.POST.get("new_password", None)

        if not(old_password and new_password):
            return JsonResponse({"message": "Old and new password required"})
        
        if old_password == new_password:
            return JsonResponse({"message": "Old password and new password cant be same", "status": 400}, status=400)
        
        if len(new_password) < 6:
            return JsonResponse({"message": "New password too short", "status": 400}, status=400)
        
        try:
            email = user.email
            auth_user = authenticate(request, email=email, password=old_password)
            if not auth_user:
                return JsonResponse({"message": "Incorrect old passsword", "status": 401}, status=401)
            
            auth_user.set_password(new_password)
            auth_user.save()

            return JsonResponse({"message":"Password updated successfully", "status":200}, status=200)
        
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"message":f"Error: {e}", "status": 500}, status=500)
            
            
        
