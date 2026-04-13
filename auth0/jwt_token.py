import jwt
import datetime
from decouple import config
from main.utils import home_tz

SECRET_KEY = config("SECRET_KEY", default="B85GBWT84VUD32JBCLA5RA5N")

def generate_jwt(user_data):
    issue_at = datetime.datetime.now(tz=home_tz)
    expiration_time = issue_at + datetime.timedelta(hours=6)

    # Payload data for the JWT
    payload = {
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "uid": user_data.get("uid"),
        "imageUrl": user_data.get("imageUrl"),
        "exp": int(expiration_time.timestamp()),  # Expiration time
        "iat": int(issue_at.timestamp()),  # Issued at
    }
    # Generate the JWT token
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    token if isinstance(token, str) else token.decode('utf-8')
    return token

def decode_jwt(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        print(f"Exception {e}")
        return None