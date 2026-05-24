import bcrypt

from models.user import User
from repositories.user_repository import UserRepository
from services.errors import AuthError


class AuthService:

    @staticmethod
    def count_users() -> int:
        return UserRepository.count()

    @staticmethod
    def get_all_users():
        return UserRepository.get_all()

    @staticmethod
    def login(username: str, password: str) -> User:
        if not username or not password:
            raise AuthError("Συμπληρώστε όνομα χρήστη και κωδικό.")

        row = UserRepository.find_by_username(username.strip())
        if row is None:
            raise AuthError("Λάθος όνομα χρήστη ή κωδικός.")
        if not row["is_active"]:
            raise AuthError("Ο λογαριασμός σας είναι ανενεργός.")
        if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            raise AuthError("Λάθος όνομα χρήστη ή κωδικός.")

        return UserRepository.row_to_user(row)

    @staticmethod
    def register_customer(
            username: str,
            email: str,
            password: str,
            first_name: str,
            last_name: str,
            phone: str = "",
    ) -> User:
        username = username.strip()
        email = email.strip()
        first_name = first_name.strip()
        last_name = last_name.strip()

        errors = []
        if not username:
            errors.append("Το όνομα χρήστη είναι υποχρεωτικό.")
        if not password:
            errors.append("Ο κωδικός είναι υποχρεωτικό.")
        if not email:
            errors.append("Το email είναι υποχρεωτικό.")
        if not first_name:
            errors.append("Το όνομα είναι υποχρεωτικό.")
        if not last_name:
            errors.append("Το επίθετο είναι υποχρεωτικό.")
        if errors:
            raise AuthError("\n".join(errors))
        if UserRepository.exists_username(username):
            raise AuthError("Το όνομα χρήστη χρησιμοποιείται ήδη.")
        if UserRepository.exists_email(email):
            raise AuthError("Το email χρησιμοποιείται ήδη.")



        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        role_id = UserRepository.get_role_id("customer")
        user_id = UserRepository.create(
            username, email, pw_hash, first_name, last_name, phone or None, role_id
        )

        return User(
            id=user_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone or None,
            role_name="customer",
            role_display="Πελάτης",
            is_active=True,
        )
