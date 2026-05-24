from __future__ import annotations
from models.user import User


class Session:
    _current_user: User | None = None

    @classmethod
    def login(cls, user: User) -> None:
        cls._current_user = user

    @classmethod
    def logout(cls) -> None:
        cls._current_user = None

    @classmethod
    def current_user(cls) -> User | None:
        return cls._current_user

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._current_user is not None
