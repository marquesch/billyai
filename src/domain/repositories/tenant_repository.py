from typing import Protocol
from typing import runtime_checkable

from domain.entities import Tenant


@runtime_checkable
class TenantRepository(Protocol):
    def create(self) -> Tenant: ...
