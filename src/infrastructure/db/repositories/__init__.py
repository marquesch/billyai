from sqlalchemy.orm import Session


class DBRepository:
    def __init__(self, session: Session):
        self.session = session
