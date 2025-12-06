from domain.entities import User
from domain.exceptions import ResourceNotFoundException
from infrastructure.persistence.database.models import DBUser
from infrastructure.persistence.database.repositories import DBRepository


class DBUserRepository(DBRepository):
    def get_by_phone_number(self, phone_number: str) -> User | None:
        db_user = self.session.query(DBUser).filter_by(phone_number=phone_number).first()

        return db_user.to_entity() if db_user is not None else None

    def get_by_id(self, user_id: int) -> User:
        db_user = self.session.query(DBUser).get(user_id)

        if db_user is None:
            raise ResourceNotFoundException

        return db_user.to_entity()
