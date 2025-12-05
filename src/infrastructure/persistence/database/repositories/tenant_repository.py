from domain.entities import Tenant
from infrastructure.persistence.database.models import DBTenant
from infrastructure.persistence.database.repositories import DBRepository


class DBTenantRepository(DBRepository):
    def create(self) -> Tenant:
        db_tenant = DBTenant()

        self.session.add(db_tenant)
        self.session.flush()
        self.session.refresh(db_tenant)

        return db_tenant.to_entity()
