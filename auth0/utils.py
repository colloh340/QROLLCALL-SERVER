from auth0.jwt_token import decode_jwt
from django.contrib.auth import get_user_model
import datetime
from decouple import config
from main.utils import home_tz

APP_NAME = config("APP_NAME", default=None)
WEB_APP = config("WEB_APP", default=None)

def verify_client(request):
    client_header = request.headers.get("Client")
    print(f"Client header {client_header}")
    if WEB_APP and APP_NAME:
        if client_header == WEB_APP or client_header == APP_NAME:
            return True, {"message": "Verified","status": 200}
        else:
            return False, {"message": "Unathorised", "status": 403}
    else:
        return False, {"message": "Error occured.", "status":500}
    
def check_auth(request):
    auth_header = request.headers.get("Authorization")
    client_header = request.headers.get("Client")

    if client_header is not None and auth_header:
        try:
            prefix, token = auth_header.split(" ")
            if prefix.lower() == "bearer":
                if token == "none":
                    return False, {
                            "message": "Not authorized. Try Login", 
                            "status": 401
                        }
                else:
                    decoded_token = decode_jwt(token)

                    if decoded_token:
                        exp = decoded_token.get("exp")
                        current_time = datetime.datetime.now(tz=home_tz).timestamp()
                        User = get_user_model()
                        user = User.objects.get(email=decoded_token["email"])
                        if user and user.is_authenticated and current_time < exp:
                            response = {
                                    "username": decoded_token["username"],
                                    "email": decoded_token["email"],
                                    "uid": decoded_token["uid"],
                                    "imageUrl": decoded_token["imageUrl"],
                                    "token": token,
                                    "status": 200
                            }
                            if client_header == APP_NAME:
                                return True, response
                            else:
                                return False,{
                                        "message":"Insecure connection",
                                        "status": 401
                                    }
                        return False, {
                                "message": "Session expired. Login",
                                "status": 402
                            }
                    else:
                        return False, {
                            "message": "Session expired. Login",
                            "status": 401
                            }
            return False,{
                "message":"Unauthorized. Try Login.",
                "status": 401
                }
        except Exception as e:
            print(f"Exception token {e}")
            return False, {
                "message":f"Unauthorized. {e}",
                "status": 401
                }
    return False, {
        "message":"Unauthorized. No headers.",
        "status": 401
        }