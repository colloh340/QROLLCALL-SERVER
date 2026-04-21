from geopy.distance import geodesic 
from decouple import config
import pytz
import os
from django.conf import settings

time_zone = config("TIME_ZONE", default="Africa/Nairobi")

home_tz = pytz.timezone(time_zone)

image_logo_path = os.path.join(settings.BASE_DIR, "static/img/ic_logo.png")


def is_admin(user):
    return user.groups.filter(name="admin").exists()

def is_staff(user):
    return user.groups.filter(name="staff").exists()

def is_student(user):
    return user.groups.filter(name="Students").exists()

def location_radius(data = {}):
    if data is not None:
        try:
            vlat = data["venue_location"]["vlat"]
            vlog = data["venue_location"]["vlog"]
            student_vlat = data["student_location"]["slat"]
            student_vlog = data["student_location"]["slog"]

            venue_location = (vlat, vlog)
            student_location = (student_vlat, student_vlog)

            distance = geodesic(venue_location, student_location).meters
            return True, {
                "distance": distance,
                "message": "Distance calculated successfully",
                "status": 200
            }
        except Exception as e:
            print(f"Error: {e}")
            return False, {
                "message": f"Error: {e}",
                "status": 500
            }
    else:
        return False, {
            "message": "No data provided",
            "status": 400
        }
