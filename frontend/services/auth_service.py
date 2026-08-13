from services import api_client
from utils.session import set_auth


def login(email: str, password: str) -> dict:
    result = api_client.post("/auth/login", {"email": email, "password": password})
    if "error" not in result:
        set_auth(result["access_token"], result)
    return result


def get_me() -> dict:
    return api_client.get("/auth/me")


def logout_api() -> dict:
    return api_client.post("/auth/logout", {})
