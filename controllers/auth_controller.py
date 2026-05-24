from models.user import User
from services.auth_service import AuthService
from services.errors import AuthError  # re-exported για τα views

__all__ = ["AuthController", "AuthError"]


class AuthController:

    @staticmethod
    def count_users() -> int:
        return AuthService.count_users()

    @staticmethod
    def get_all_users():
        return AuthService.get_all_users()

    @staticmethod
    def login(username: str, password: str) -> User:
        return AuthService.login(username, password)

    @staticmethod
    def register_customer(
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: str = "",
    ) -> User:
        return AuthService.register_customer(
            username, email, password, first_name, last_name, phone
        )
