from typing import Optional
from app.models.user import User


class IUserRepository:

    def find_by_id(self, user_id: int) -> Optional[User]:
        pass

    def find_by_username(self, username: str) -> Optional[User]:
        pass

    def save(self, user: User) -> None:
        pass
