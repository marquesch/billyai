import datetime
from dataclasses import dataclass
from enum import Enum


class MessageBroker(Enum):
    WHATSAPP = "WHATSAPP"
    API = "API"


class MessageAuthor(Enum):
    USER = "USER"
    BILLY = "BILLY"
    SYSTEM = "SYSTEM"


@dataclass
class Tenant:
    id: int


@dataclass
class User:
    id: int
    phone_number: str
    name: str
    is_registered: bool
    tenant_id: int


@dataclass
class Bill:
    id: int
    value: float
    date: datetime.date
    category_id: int
    tenant_id: int


@dataclass
class Category:
    id: int
    name: str
    description: str
    tenant_id: int


@dataclass
class Message:
    id: int
    body: str
    author: str
    timestamp: datetime.datetime
    broker: str
    external_message_id: str | None
    user_id: int
    tenant_id: int
