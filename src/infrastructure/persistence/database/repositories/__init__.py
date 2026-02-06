from sqlalchemy.orm import Session

from domain.entities import Bill
from domain.entities import Category
from domain.entities import Message
from domain.entities import Tenant
from domain.entities import User


class DBRepository:
    def __init__(self, session: Session):
        self.session = session
