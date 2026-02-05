import pytest

from domain.entities import User
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import UserNotFoundException
from infrastructure.persistence.database.models import DBTenant
from infrastructure.persistence.database.models import DBUser
from infrastructure.persistence.database.repositories.user_repository import DBUserRepository


class TestDBUserRepositoryGetByPhoneNumber:
    def test_get_existing_user_by_phone_number(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
    ):
        user = db_user_repository.get_by_phone_number(phone_number=db_user.phone_number)

        assert isinstance(user, User)
        assert user.id == db_user.id
        assert user.phone_number == db_user.phone_number
        assert user.name == db_user.name
        assert user.tenant_id == db_user.tenant_id
        assert user.is_registered == db_user.is_registered

    def test_get_nonexistent_user_by_phone_number(self, db_user_repository: DBUserRepository):
        user = db_user_repository.get_by_phone_number(phone_number="+5511999999999")

        assert user is None


class TestDBUserRepositoryGetById:
    def test_get_existing_user_by_id(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
    ):
        user = db_user_repository.get_by_id(user_id=db_user.id)

        assert isinstance(user, User)
        assert user.id == db_user.id
        assert user.phone_number == db_user.phone_number
        assert user.name == db_user.name
        assert user.tenant_id == db_user.tenant_id
        assert user.is_registered == db_user.is_registered

    def test_get_nonexistent_user_by_id(self, db_user_repository: DBUserRepository):
        with pytest.raises(UserNotFoundException):
            db_user_repository.get_by_id(user_id=99999)


class TestDBUserRepositoryCreate:
    def test_create_user_successfully(
        self,
        db_user_repository: DBUserRepository,
        db_tenant: DBTenant,
    ):
        phone_number = "+5511987654321"
        name = "John Doe"
        is_registered = True

        user = db_user_repository.create(
            phone_number=phone_number,
            name=name,
            tenant_id=db_tenant.id,
            is_registered=is_registered,
        )

        assert isinstance(user, User)
        assert user.phone_number == phone_number
        assert user.name == name
        assert user.tenant_id == db_tenant.id
        assert user.is_registered == is_registered
        assert user.id is not None

    def test_create_unregistered_user(
        self,
        db_user_repository: DBUserRepository,
        db_tenant: DBTenant,
    ):
        phone_number = "+5511987654321"
        name = "Jane Doe"
        is_registered = False

        user = db_user_repository.create(
            phone_number=phone_number,
            name=name,
            tenant_id=db_tenant.id,
            is_registered=is_registered,
        )

        assert user.is_registered is False

    def test_create_user_with_duplicate_phone_number(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        with pytest.raises(PhoneNumberTakenException):
            db_user_repository.create(
                phone_number=db_user.phone_number,
                name="Another User",
                tenant_id=db_tenant.id,
                is_registered=True,
            )


class TestDBUserRepositoryUpdate:
    def test_update_user_name(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        new_name = "Updated Name"
        original_is_registered = db_user.is_registered

        updated_user = db_user_repository.update(
            user_id=db_user.id,
            tenant_id=db_tenant.id,
            name=new_name,
            is_registered=original_is_registered,
        )

        assert updated_user.name == new_name
        assert updated_user.is_registered == original_is_registered

    def test_update_user_registration_status(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        original_name = db_user.name
        new_is_registered = not db_user.is_registered

        updated_user = db_user_repository.update(
            user_id=db_user.id,
            tenant_id=db_tenant.id,
            name=original_name,
            is_registered=new_is_registered,
        )

        assert updated_user.name == original_name
        assert updated_user.is_registered == new_is_registered

    def test_update_user_multiple_fields(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        new_name = "Completely New Name"
        new_is_registered = not db_user.is_registered

        updated_user = db_user_repository.update(
            user_id=db_user.id,
            tenant_id=db_tenant.id,
            name=new_name,
            is_registered=new_is_registered,
        )

        assert updated_user.name == new_name
        assert updated_user.is_registered == new_is_registered

    def test_update_nonexistent_user(
        self,
        db_user_repository: DBUserRepository,
        db_tenant: DBTenant,
    ):
        with pytest.raises(UserNotFoundException):
            db_user_repository.update(
                user_id=99999,
                tenant_id=db_tenant.id,
                name="Some Name",
                is_registered=True,
            )

    def test_update_user_from_different_tenant(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
        another_db_tenant: DBTenant,
    ):
        with pytest.raises(UserNotFoundException):
            db_user_repository.update(
                user_id=db_user.id,
                tenant_id=another_db_tenant.id,
                name="Updated Name",
                is_registered=True,
            )


class TestDBUserRepositoryEdgeCases:
    def test_create_user_with_empty_name(
        self,
        db_user_repository: DBUserRepository,
        db_tenant: DBTenant,
    ):
        phone_number = "+5511987654321"
        name = ""
        is_registered = True

        user = db_user_repository.create(
            phone_number=phone_number,
            name=name,
            tenant_id=db_tenant.id,
            is_registered=is_registered,
        )

        assert user.name == ""

    def test_create_user_with_very_long_name(
        self,
        db_user_repository: DBUserRepository,
        db_tenant: DBTenant,
    ):
        phone_number = "+5511987654321"
        name = "A" * 500
        is_registered = True

        user = db_user_repository.create(
            phone_number=phone_number,
            name=name,
            tenant_id=db_tenant.id,
            is_registered=is_registered,
        )

        assert user.name == name

    def test_update_user_phone_number_remains_unchanged(
        self,
        db_user_repository: DBUserRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        original_phone_number = db_user.phone_number

        updated_user = db_user_repository.update(
            user_id=db_user.id,
            tenant_id=db_tenant.id,
            name="New Name",
            is_registered=True,
        )

        assert updated_user.phone_number == original_phone_number

    def test_get_by_phone_number_with_special_characters(
        self,
        db_user_repository: DBUserRepository,
    ):
        user = db_user_repository.get_by_phone_number(phone_number="+55 (11) 98765-4321")

        assert user is None
