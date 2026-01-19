from domain.entities import Bill
from domain.entities import Category
from domain.entities import Message
from domain.entities import Tenant
from domain.entities import User


class InMemoryDatabase:
    def __init__(self):
        self.users: dict[int, User] = {}
        self.users_id_seq: int = 0
        self.bills: dict[int, Bill] = {}
        self.bills_id_seq: int = 0
        self.categories: dict[int, Category] = {}
        self.categories_id_seq: int = 0
        self.messages: dict[int, Message] = {}
        self.messages_id_seq: int = 0
        self.tenants: dict[int, Tenant] = {}
        self.tenants_id_seq: int = 0


class InMemoryRepository:
    def __init__(self, in_memory_database: InMemoryDatabase):
        self._in_memory_database = in_memory_database
