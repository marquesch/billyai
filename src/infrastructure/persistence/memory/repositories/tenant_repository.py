from domain.entities import Tenant
from infrastructure.persistence.memory.repositories import InMemoryRepository


class InMemoryTenantRepository(InMemoryRepository):
    def create(self) -> Tenant:
        self._in_memory_database.tenants_id_seq += 1
        tenant = Tenant(id=self._in_memory_database.tenants_id_seq)

        self._in_memory_database.tenants[self._in_memory_database.tenants_id_seq] = tenant
