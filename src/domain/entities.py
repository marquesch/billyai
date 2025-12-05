import datetime
from dataclasses import dataclass


@dataclass
class Tenant:
    id: int


@dataclass
class User:
    id: int
    phone_number: str
    name: str
    tenant_id: int


@dataclass
class Bill:
    id: int
    value: float
    date: datetime.datetime
    category_id: int
    tenant_id: int


@dataclass
class Category:
    id: int
    name: str
    description: str
