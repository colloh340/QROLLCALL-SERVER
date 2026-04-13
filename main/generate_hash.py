import hashlib
import time
import secrets
class Generator:
    def __init__(self, value) -> None:
        # current_time_millis = int(time.time() * 1000)
        # concatenated_string = f"{current_time_millis} {value}"
        # self.hashed_string = hashlib.sha256(concatenated_string.encode()).hexdigest()
        self.hashed_string = secrets.token_urlsafe(32)

    def __str__(self) -> str:
        return str(self.hashed_string)
    