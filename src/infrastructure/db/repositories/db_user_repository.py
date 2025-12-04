from domain.entities import User
from infrastructure.db.models import DBUser
from infrastructure.db.repositories import DBRepository
from infrastructure.db.repositories.exceptions import ResourceNotFoundException


class DBUserRepository(DBRepository):
    def get_by_phone_number(self, phone_number: str) -> User:
        db_user = self.session.query(DBUser).filter(phone_number=phone_number).first()

        if db_user is None:
            raise ResourceNotFoundException

        return db_user.to_entity()
