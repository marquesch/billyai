from sqlalchemy.orm import Session

from domain.entities import Bill
from domain.entities import Category
from domain.entities import Message
from domain.entities import Tenant
from domain.entities import User


class DBRepository:
    def __init__(self, session: Session):
        self.session = session


class InMemoryRepository:
    def __init__(self, *args, **kwargs):
        self._bills: dict[int, Bill] = {}
        self._bills_id_seq: int = 0
        self._users: dict[int, User] = {}
        self._users_id_seq: int = 0
        self._categories: dict[int, Category] = {}
        self._categories_id_seq: int = 0
        self._messages: dict[int, Message] = {}
        self._messages_id_seq: int = 0
        self._tenants: dict[int, Tenant] = {}
        self._tenants_id_seq: int = 0
