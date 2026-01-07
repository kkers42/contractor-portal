import os

class AuthSettings:
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
    APP_JWT_SECRET = os.getenv("APP_JWT_SECRET", "CHANGE_ME")
    APP_JWT_ISS = "contractor-portal"
    APP_JWT_EXP_MIN = int(os.getenv("APP_JWT_EXP_MIN", "120"))

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    MS_TENANT = os.getenv("MS_TENANT", "common")
    MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
    MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
    @property
    def MS_DISCOVERY_URL(self):
        return f"https://login.microsoftonline.com/{self.MS_TENANT}/v2.0/.well-known/openid-configuration"

settings = AuthSettings()
