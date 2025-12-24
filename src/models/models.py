from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserData:
    """Данные пользователя"""
    user_id: int
    username: str = None
    first_name: str = None
    last_name: str = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or "Аноним"