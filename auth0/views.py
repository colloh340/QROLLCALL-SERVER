from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import login, authenticate, logout
from decouple import config, Csv
from .jwt_token import decode_jwt, generate_jwt
from django.contrib.auth import get_user_model
from main.generate_hash import Generator
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from main.utils import is_admin, is_staff
SECRET_KEY = config("SECRET_KEY", default="B85GBWT84VUD32JBCLA5RA5N")
APP_NAME = config("APP_NAME", default=None)

# Create your views here.
@csrf_exempt
def login_view_android(request):
    auth_header = request.headers.get("Authorization")
    client_header = request.headers.get("Client")
    print(f"Header auth: {auth_header}")
    if auth_header:
        try:
            prefix, token = auth_header.split(" ")
            if prefix.lower() == "bearer":
                if request.method == "POST":
                    #not logged in. Login user
                    raw_body = request.body
                    data = json.loads(raw_body)
                    email = data.get("email", None)
                    password = data.get("password", None)
                    remember_me = data.get("remember_me", False)

                    if client_header == APP_NAME:
                        if password and email:
                            response = login_user(request,email,password)
                            if response:
                                print("Logged in successfully")
                                return JsonResponse(response, status=200)
                        return JsonResponse({"message":"Invalid credentials", "status":401}, status=401)
                    else:
                        return JsonResponse({"message":"Insure connection", "status":401}, status=401)
                else:
                    return JsonResponse({"message":"Bad Request."}, status=400)
        except Exception as e:
            JsonResponse({"message": "Incorrect authorization key."}, status=401)
    return JsonResponse({"message":"Not authorized to access service."}, status=401)

def login_web(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        if email and password:
            response = login_user(request,email,password)
            if response:
                return JsonResponse(response, status=200)
            else:
                return JsonResponse({"message":"Invalid credentials", "status":401},status=401)
        else:
            return JsonResponse({"message":"Email and password required"}, status=401)
    elif request.method  == "GET":
        return render(request, "login.html", {
            "user":request.user,
            "is_admin":is_admin(request.user),
            "is_staff": is_staff(request.user)
            })

def register(request):
    if request.method == "POST":
        return JsonResponse({"username":"Anthony"})
    return JsonResponse({"message":"invalid method"})

def create_user_account(data={}):
    if not data:
        return False, {"message": "No data provided", "status": 400}

    # Extract user data safely
    email = data.get("email")
    password = data.get("password")
    account_created_on = data.get("account_created_on")
    user_type = data.get("type_id")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    image_url = data.get("image_url", "")

    # Validate required fields
    if not all([email, password, user_type, first_name, last_name]):
        return False, {"message": "Missing required fields", "status": 400}

    # Check if user already exists
    User = get_user_model()
    if User.objects.filter(email=email).exists():
        return False, {"message": "User with this email already exists", "status": 409}

    # Generate User ID and assign user group
    user_groups = {
        "student": "Students",
        "staff": "Staff",
        "admin": "Admin"
    }

    if user_type not in user_groups:
        return False, {"message": "Invalid user type", "status": 400}

    userId = f"{user_type}_{Generator(email)}"
    user_group = user_groups[user_type]

    # Create user
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            account_created_on=account_created_on,
            first_name=first_name,
            last_name=last_name,
            userId=userId,
            token="none",
            image_url=image_url
        )

        # Assign user to group
        group_name, _ = create_group(user_group)
        group_name.user_set.add(user)

        return True, user
    except Exception as e:
        return False, {"message": f"Error creating account: {str(e)}", "status": 500}
        
def create_group(group_name):
    return Group.objects.get_or_create(name=group_name)

def login_user(request, email,password):
    try:
        user = authenticate(request=request, email=email,password=password)
        if user is not None:
            login(request, user=user)
            
            last_name = user.last_name
            first_name = user.first_name
            user_id = user.userId
            image_url = user.image_url
            user_data = {
                "username": f"{first_name} {last_name}",
                "email": email,
                "uid": user_id,
                "imageUrl": image_url,
            }
            # Generate token
            token = generate_jwt(user_data)
            user.token = token
            user.save()
            # Prepare the JSON response
            response = {
                "message":"success",
                "username": user_data["username"],
                "email": user_data["email"],
                "uid": user_data["uid"],
                "imageUrl": user_data["imageUrl"],
                "token": token,  # Add the JWT token
                "status": 200
            }
            return response
        else:
            return None
    except Exception as e:
        print(f"Error {e}")
        return None
    
def logout_view(request):
    logout(request)
    return redirect("/")
